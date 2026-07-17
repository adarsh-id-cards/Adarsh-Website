import json
from io import BytesIO
from urllib.parse import parse_qs, urlsplit
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from website.models import ContactSubmission, PortfolioCategory, PortfolioItem, Testimonial as WebsiteTestimonial
from website.services import PortfolioItemService, TestimonialService
from website.views import pwa_manifest


User = get_user_model()


class PortfolioUploadProcessingTests(TestCase):
	def setUp(self):
		cache.clear()
		self.category = PortfolioCategory.objects.create(name='Test Category')
		self.other_category = PortfolioCategory.objects.create(name='Updated Category')

	def _uploaded_image(self, name='sample.jpg'):
		buffer = BytesIO()
		Image.new('RGB', (1200, 800), color=(210, 80, 90)).save(buffer, format='JPEG', quality=95)
		buffer.seek(0)
		return SimpleUploadedFile(name, buffer.read(), content_type='image/jpeg')

	def _uploaded_video(self, name='sample.mp4'):
		return SimpleUploadedFile(name, b'fake-video-content', content_type='video/mp4')

	def test_direct_model_save_processes_portfolio_image_to_webp(self):
		item = PortfolioItem.objects.create(
			title='Direct Model Upload',
			category=self.category,
			item_type='image',
			image=self._uploaded_image('direct.jpg'),
		)

		self.assertTrue(item.image.name.lower().endswith('.webp'))
		self.assertLessEqual(item.image.size, 200 * 1024)

	def test_service_create_processes_portfolio_image_to_webp(self):
		item = PortfolioItemService.create(
			category_id=self.category.id,
			item_type='image',
			image=self._uploaded_image('service.jpg'),
			is_active=True,
		)

		self.assertTrue(item.image.name.lower().endswith('.webp'))
		self.assertLessEqual(item.image.size, 200 * 1024)

	def test_service_update_renames_title_when_category_changes(self):
		item = PortfolioItemService.create(
			category_id=self.category.id,
			item_type='image',
			image=self._uploaded_image('rename-source.jpg'),
			is_active=True,
		)
		old_title = item.title

		PortfolioItemService.update(item.id, category_id=self.other_category.id)
		item.refresh_from_db()

		self.assertEqual(item.category_id, self.other_category.id)
		self.assertNotEqual(item.title, old_title)
		self.assertTrue(item.title.startswith(self.other_category.name + ' '))
		suffix = item.title.split(' ')[-1]
		self.assertEqual(len(suffix), 6)
		self.assertTrue(all(ch in '0123456789ABCDEF' for ch in suffix))

	def test_service_update_switch_to_image_clears_video_sources(self):
		item = PortfolioItemService.create(
			category_id=self.category.id,
			item_type='reel',
			video_file=self._uploaded_video('intro.mp4'),
			is_active=True,
		)

		PortfolioItemService.update(
			item.id,
			item_type='image',
			image=self._uploaded_image('converted-image.jpg'),
		)
		item.refresh_from_db()

		self.assertEqual(item.item_type, 'image')
		self.assertFalse(bool(item.video_file))
		self.assertEqual(item.video_url, '')

	def test_home_products_rows_exclude_reels_and_videos(self):
		image_item = PortfolioItemService.create(
			category_id=self.category.id,
			item_type='image',
			image=self._uploaded_image('home-image.jpg'),
			is_active=True,
			is_featured=True,
		)
		reel_item = PortfolioItemService.create(
			category_id=self.category.id,
			item_type='reel',
			video_file=self._uploaded_video('home-reel.mp4'),
			is_active=True,
			is_featured=True,
		)
		cache.delete('home_sections')

		response = self.client.get('/')
		self.assertEqual(response.status_code, 200)

		row_items = list(response.context['row1_portfolio']) + list(response.context['row2_portfolio'])
		self.assertTrue(row_items)
		self.assertIn(image_item, row_items)
		self.assertNotIn(reel_item, row_items)
		self.assertTrue(all(p.item_type == 'image' for p in row_items))

	def test_home_products_rows_mix_categories_without_adjacent_repeats(self):
		cat_a = PortfolioCategory.objects.create(name='Category A')
		cat_b = PortfolioCategory.objects.create(name='Category B')
		cat_c = PortfolioCategory.objects.create(name='Category C')

		for idx in range(2):
			PortfolioItemService.create(
				category_id=cat_a.id,
				item_type='image',
				image=self._uploaded_image(f'cat-a-{idx}.jpg'),
				is_active=True,
				is_featured=True,
			)
			PortfolioItemService.create(
				category_id=cat_b.id,
				item_type='image',
				image=self._uploaded_image(f'cat-b-{idx}.jpg'),
				is_active=True,
				is_featured=True,
			)
			PortfolioItemService.create(
				category_id=cat_c.id,
				item_type='image',
				image=self._uploaded_image(f'cat-c-{idx}.jpg'),
				is_active=True,
				is_featured=True,
			)

		cache.delete('home_sections')
		response = self.client.get('/')
		self.assertEqual(response.status_code, 200)

		row1 = list(response.context['row1_portfolio'])
		row2 = list(response.context['row2_portfolio'])
		self.assertTrue(row1)
		self.assertTrue(row2)

		for row in (row1, row2):
			for i in range(1, len(row)):
				self.assertNotEqual(row[i - 1].category_id, row[i].category_id)

		for i in range(min(len(row1), len(row2))):
			self.assertNotEqual(row1[i].category_id, row2[i].category_id)


class TestimonialSubmissionTests(TestCase):
	def setUp(self):
		cache.clear()

	def _uploaded_image(self, name='feedback.png'):
		buffer = BytesIO()
		Image.new('RGB', (800, 500), color=(55, 120, 220)).save(buffer, format='PNG')
		buffer.seek(0)
		return SimpleUploadedFile(name, buffer.read(), content_type='image/png')

	def test_public_submission_blocks_duplicate_email_or_ip(self):
		TestimonialService.create_public(
			reviewer_name='Parent One',
			reviewer_email='parent@example.com',
			reviewer_school='Example School',
			text='Great service.',
			rating=5,
			reviewer_ip='8.8.8.8',
		)

		with self.assertRaises(ValidationError) as email_error:
			TestimonialService.create_public(
				reviewer_name='Parent Two',
				reviewer_email='parent@example.com',
				reviewer_school='Example School',
				text='Second review.',
				rating=4,
				reviewer_ip='1.1.1.1',
			)
		self.assertIn('A review has already been submitted from this email address or device.', str(email_error.exception))

		with self.assertRaises(ValidationError) as ip_error:
			TestimonialService.create_public(
				reviewer_name='Parent Three',
				reviewer_email='other@example.com',
				reviewer_school='Example School',
				text='Third review.',
				rating=4,
				reviewer_ip='8.8.8.8',
			)
		self.assertIn('A review has already been submitted from this email address or device.', str(ip_error.exception))

	def test_public_testimonials_page_hides_review_cta_for_existing_email(self):
		user = User.objects.create_user(
			username='viewer@example.com',
			email='viewer@example.com',
			password='testpass123',
			role='client',
		)
		WebsiteTestimonial.objects.create(
			reviewer_name='Viewer',
			reviewer_email='viewer@example.com',
			reviewer_school='Demo School',
			text='Nice work.',
			rating=5,
			is_active=False,
		)

		self.client.force_login(user)
		response = self.client.get(reverse('website:testimonials'))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.context['can_submit_public_review'])

	def test_public_testimonial_submit_rejects_duplicate_ip(self):
		TestimonialService.create_public(
			reviewer_name='Parent One',
			reviewer_email='parent2@example.com',
			reviewer_school='Example School',
			text='Great service.',
			rating=5,
			reviewer_ip='9.9.9.9',
		)

		response = self.client.post(
			reverse('website:submit_testimonial'),
			{
				'name': 'Another Parent',
				'email': 'new@example.com',
				'school': 'Example School',
				'text': 'Another review.',
				'rating': '5',
			},
			HTTP_X_FORWARDED_FOR='9.9.9.9',
		)

		self.assertEqual(response.status_code, 400)
		self.assertJSONEqual(response.content, {
			'success': False,
			'message': 'A review has already been submitted from this email address or device.',
		})

	def test_public_testimonials_page_authenticated_user_not_blocked_by_shared_ip(self):
		user = User.objects.create_user(
			username='client-unique@example.com',
			email='client-unique@example.com',
			password='testpass123',
			role='client',
		)

		WebsiteTestimonial.objects.create(
			reviewer_name='Other User',
			reviewer_email='other-user@example.com',
			reviewer_ip='5.5.5.5',
			reviewer_school='Example School',
			text='Existing review from shared device/network.',
			rating=5,
			is_active=False,
		)

		self.client.force_login(user)
		response = self.client.get(reverse('website:testimonials'), REMOTE_ADDR='5.5.5.5')

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['can_submit_public_review'])

	def test_public_testimonial_submit_accepts_attachment_image(self):
		response = self.client.post(
			reverse('website:submit_testimonial'),
			{
				'name': 'Attachment User',
				'email': 'attachment-user@example.com',
				'school': 'Attachment School',
				'text': 'Sharing screenshot proof.',
				'rating': '4',
				'attachment_image': self._uploaded_image(),
			},
			HTTP_X_FORWARDED_FOR='4.4.4.4',
		)

		self.assertEqual(response.status_code, 200)
		created = WebsiteTestimonial.objects.get(reviewer_email='attachment-user@example.com')
		self.assertTrue(bool(created.attachment_image))


class WebsitePublicHardeningTests(TestCase):
	def setUp(self):
		cache.clear()

	def test_submit_contact_sanitizes_subject_before_save(self):
		response = self.client.post(
			reverse('website:submit_contact'),
			{
				'name': 'Contact User',
				'email': 'contact-user@example.com',
				'phone': '9999999999',
				'subject': 'Need help\r\nBcc: hidden@example.com',
				'message': 'Please call me back.',
			},
		)

		self.assertEqual(response.status_code, 200)
		submission = ContactSubmission.objects.get(email='contact-user@example.com')
		self.assertEqual(submission.subject, 'Need help Bcc: hidden@example.com')
		self.assertNotIn('\r', submission.subject)
		self.assertNotIn('\n', submission.subject)


class WebsitePwaInstallabilityTests(TestCase):
	def test_manifest_endpoint_returns_installable_payload(self):
		response = self.client.get(reverse('website:pwa_manifest'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['Content-Type'], 'application/manifest+json')
		payload = response.json()
		self.assertEqual(payload.get('start_url'), '/dash/auth/login/?src=pwa-launch')
		self.assertEqual(payload.get('scope'), '/')
		self.assertEqual(payload.get('display'), 'standalone')
		self.assertGreaterEqual(len(payload.get('icons', [])), 1)

	def test_service_worker_endpoint_returns_required_headers(self):
		response = self.client.get(reverse('website:pwa_service_worker'))

		self.assertEqual(response.status_code, 200)
		self.assertIn('javascript', response['Content-Type'])
		self.assertEqual(response['Service-Worker-Allowed'], '/')
		self.assertIn("self.addEventListener('fetch'", response.content.decode('utf-8'))


class WebsiteSingletonServicesTests(TestCase):
	def setUp(self):
		cache.clear()
		from website.models import BusinessDetails, WebsiteStatus
		BusinessDetails.objects.all().delete()
		WebsiteStatus.objects.all().delete()

	def test_business_details_update_handles_non_one_pk(self):
		from website.models import BusinessDetails
		from website.services import BusinessDetailsService
		# Create a record with pk=2
		BusinessDetails.objects.create(id=2, site_name="Existing Site")

		# Update details using the service layer
		updated = BusinessDetailsService.update({'site_name': 'New Site Name'})

		# Check that it updated the existing record rather than failing or creating another
		self.assertEqual(BusinessDetails.objects.count(), 1)
		self.assertEqual(updated.id, 2)
		self.assertEqual(updated.site_name, 'New Site Name')

	def test_website_status_toggle_handles_non_one_pk(self):
		from website.models import WebsiteStatus
		from website.services import WebsiteStatusService
		# Create a record with pk=2
		status_obj = WebsiteStatus.objects.create(id=2, status='live')

		# Toggle status using the service layer
		new_status = WebsiteStatusService.toggle_status()

		# Check that it updated the existing record
		self.assertEqual(WebsiteStatus.objects.count(), 1)
		self.assertEqual(new_status, 'draft')
		status_obj.refresh_from_db()
		self.assertEqual(status_obj.status, 'draft')
		self.assertEqual(status_obj.id, 2)


class WebsiteClientLogoTests(TestCase):
	def setUp(self):
		cache.clear()
		cache.set('panel_clients_sync_done', True, 600)  # Bypass API requests in setup for view tests
		from website.models import BusinessDetails
		BusinessDetails.objects.all().delete()
		BusinessDetails.objects.create(site_name="Test Site")

	def _uploaded_image(self, name='sample.jpg'):
		buffer = BytesIO()
		Image.new('RGB', (1200, 800), color=(210, 80, 90)).save(buffer, format='JPEG', quality=95)
		buffer.seek(0)
		return SimpleUploadedFile(name, buffer.read(), content_type='image/jpeg')

	def test_website_client_logo_property(self):
		from website.models import WebsiteClientLogo
		client_logo = WebsiteClientLogo(
			name="Test Client",
			logo=self._uploaded_image(),
			website_is_visible=True,
			website_display_order=0
		)
		self.assertEqual(client_logo.website_logo, client_logo.logo)

	def test_homepage_includes_trusted_clients(self):
		from website.models import WebsiteClientLogo
		# Create a client logo
		WebsiteClientLogo.objects.create(
			name="Adarsh Partner",
			email="partner@example.com",
			logo=self._uploaded_image(),
			website_is_visible=True,
			website_display_order=1
		)

		response = self.client.get(reverse('website:home'))
		self.assertEqual(response.status_code, 200)
		self.assertIn('trusted_clients', response.context)
		self.assertEqual(len(response.context['trusted_clients']), 1)
		self.assertEqual(response.context['trusted_clients'][0].name, "Adarsh Partner")

	def test_homepage_excludes_invisible_or_logoless_clients(self):
		from website.models import WebsiteClientLogo
		# Create a visible client with logo
		WebsiteClientLogo.objects.create(
			name="Visible Partner",
			email="visible@example.com",
			logo=self._uploaded_image(),
			website_is_visible=True,
			website_display_order=1
		)
		# Create an invisible client with logo
		WebsiteClientLogo.objects.create(
			name="Invisible Partner",
			email="invisible@example.com",
			logo=self._uploaded_image(),
			website_is_visible=False,
			website_display_order=2
		)
		# Create a visible client without logo
		WebsiteClientLogo.objects.create(
			name="No Logo Partner",
			email="nologo@example.com",
			logo=None,
			website_is_visible=True,
			website_display_order=3
		)

		response = self.client.get(reverse('website:home'))
		self.assertEqual(response.status_code, 200)
		self.assertIn('trusted_clients', response.context)
		# Only "Visible Partner" should be shown
		self.assertEqual(len(response.context['trusted_clients']), 1)
		self.assertEqual(response.context['trusted_clients'][0].name, "Visible Partner")

	@mock.patch('requests.get')
	def test_sync_from_panel_creates_updates_deletes(self, mock_get):
		from website.models import WebsiteClientLogo
		from website.services import WebsiteClientLogoService

		# 1. First sync: Mock response returns Alpha and Beta
		mock_response = mock.Mock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			'success': True,
			'clients': [
				{'name': 'Alpha School', 'email': 'alpha@example.com', 'total_records': 250},
				{'name': 'Beta School', 'email': 'beta@example.com', 'total_records': 12},
			]
		}
		mock_get.return_value = mock_response

		# Clear cache to force run
		cache.clear()

		# Run sync
		WebsiteClientLogoService.sync_from_panel()

		# Check that both are created locally with default visibility=False and logo=None
		self.assertEqual(WebsiteClientLogo.objects.count(), 2)
		alpha = WebsiteClientLogo.objects.get(email='alpha@example.com')
		beta = WebsiteClientLogo.objects.get(email='beta@example.com')
		self.assertEqual(alpha.name, 'Alpha School')
		self.assertFalse(alpha.website_is_visible)
		self.assertFalse(bool(alpha.logo))

		# 2. Second sync: Mock response updates Alpha name and removes Beta, adds Gamma
		cache.clear()
		mock_response.json.return_value = {
			'success': True,
			'clients': [
				{'name': 'Alpha School Updated', 'email': 'alpha@example.com', 'total_records': 300},
				{'name': 'Gamma School', 'email': 'gamma@example.com', 'total_records': 5},
			]
		}

		WebsiteClientLogoService.sync_from_panel()

		# Check Beta is deleted, Alpha is updated, Gamma is created
		self.assertEqual(WebsiteClientLogo.objects.count(), 2)
		self.assertFalse(WebsiteClientLogo.objects.filter(email='beta@example.com').exists())
		alpha.refresh_from_db()
		self.assertEqual(alpha.name, 'Alpha School Updated')
		gamma = WebsiteClientLogo.objects.get(email='gamma@example.com')
		self.assertEqual(gamma.name, 'Gamma School')

	@mock.patch('requests.get')
	def test_sync_from_panel_fails_gracefully(self, mock_get):
		from website.models import WebsiteClientLogo
		from website.services import WebsiteClientLogoService

		# Seed a local client
		WebsiteClientLogo.objects.create(
			name='Local Client',
			email='local@example.com',
			website_is_visible=True
		)

		# Mock API failure
		mock_get.side_effect = Exception("API connection timed out")

		cache.clear()

		# Run sync - should not raise exception and should not delete the seed data
		WebsiteClientLogoService.sync_from_panel()

		self.assertEqual(WebsiteClientLogo.objects.count(), 1)
		self.assertTrue(WebsiteClientLogo.objects.filter(email='local@example.com').exists())

	@mock.patch('requests.get')
	@mock.patch('website.services._invalidate_public_section_caches')
	def test_sync_from_panel_invalidates_cache_on_mutation(self, mock_invalidate, mock_get):
		from website.services import WebsiteClientLogoService

		# Mock response
		mock_response = mock.Mock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			'success': True,
			'clients': [
				{'name': 'Alpha School', 'email': 'alpha@example.com', 'total_records': 250},
			]
		}
		mock_get.return_value = mock_response

		cache.clear()
		WebsiteClientLogoService.sync_from_panel()
		
		# Should have mutated (created Alpha School)
		self.assertTrue(mock_invalidate.called)

		# Run again with same data
		mock_invalidate.reset_mock()
		cache.clear()
		WebsiteClientLogoService.sync_from_panel()
		
		# No mutation occurred, should not have called invalidate
		self.assertFalse(mock_invalidate.called)
