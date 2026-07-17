from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from website.models import PortfolioCategory, PortfolioItem, WebsiteClientLogo

@override_settings(WEB_APP_API_KEY='test_secret_sharing_key')
class ApiSharingTests(TestCase):
    def setUp(self):
        # Create categories
        self.cat1 = PortfolioCategory.objects.create(
            name='Test Category A',
            slug='test-category-a',
            is_active=True,
            order=0
        )
        self.cat2 = PortfolioCategory.objects.create(
            name='Test Category B',
            slug='test-category-b',
            is_active=False, # inactive category
            order=1
        )
        
        # Helper to generate in-memory dummy image
        buffer = BytesIO()
        Image.new('RGB', (100, 100), color=(255, 0, 0)).save(buffer, format='PNG')
        buffer.seek(0)
        dummy_image = SimpleUploadedFile('dummy.png', buffer.read(), content_type='image/png')
        
        buffer_logo = BytesIO()
        Image.new('RGB', (100, 100), color=(0, 255, 0)).save(buffer_logo, format='PNG')
        buffer_logo.seek(0)
        dummy_logo = SimpleUploadedFile('logo.png', buffer_logo.read(), content_type='image/png')
        
        # Create products
        self.prod1 = PortfolioItem.objects.create(
            title='Product 1',
            slug='product-1',
            category=self.cat1,
            item_type='image',
            image=dummy_image,
            is_active=True,
            order=0
        )
        
        # Create client logos
        self.client1 = WebsiteClientLogo.objects.create(
            name='Client A',
            email='clienta@example.com',
            logo=dummy_logo,
            website_is_visible=True,
            website_display_order=0,
            total_records=100
        )
        
        self.portfolio_url = reverse('api_sharing:shared_portfolio_list')
        self.clients_url = reverse('api_sharing:shared_client_list')

    def test_portfolio_unauthorized_missing_key(self):
        """Endpoints return 401 when API key is completely missing."""
        response = self.client.get(self.portfolio_url)
        self.assertEqual(response.status_code, 401)
        self.assertJSONEqual(response.content, {
            'success': False,
            'message': 'Unauthorized. A valid X-API-KEY is required.'
        })

    def test_portfolio_unauthorized_invalid_key(self):
        """Endpoints return 401 when API key is wrong."""
        response = self.client.get(self.portfolio_url, HTTP_X_API_KEY='wrong_key')
        self.assertEqual(response.status_code, 401)

    def test_portfolio_authorized_via_header(self):
        """Endpoint allows access when correct X-API-KEY header is provided."""
        response = self.client.get(self.portfolio_url, HTTP_X_API_KEY='test_secret_sharing_key')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['categories']), 1) # Only active cat1
        self.assertEqual(data['categories'][0]['name'], 'Test Category A')
        
        products = data['categories'][0]['products']
        self.assertEqual(len(products), 1) # Only active prod1
        self.assertEqual(products[0]['title'], 'Product 1')
        self.assertTrue(products[0]['media_url'].startswith('http://testserver/'))

    def test_portfolio_authorized_via_query_param(self):
        """Endpoint allows access when correct api_key query param is provided."""
        response = self.client.get(f"{self.portfolio_url}?api_key=test_secret_sharing_key")
        self.assertEqual(response.status_code, 200)

    def test_clients_list_authorized(self):
        """Endpoint lists all clients with metadata, email, and total records count."""
        response = self.client.get(self.clients_url, HTTP_X_API_KEY='test_secret_sharing_key')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['clients']), 1)
        
        client_data = data['clients'][0]
        self.assertEqual(client_data['name'], 'Client A')
        self.assertEqual(client_data['email'], 'clienta@example.com')
        self.assertEqual(client_data['total_records'], 100)
        self.assertEqual(client_data['website_is_visible'], True)
        self.assertTrue(client_data['logo_url'].startswith('http://testserver/'))
