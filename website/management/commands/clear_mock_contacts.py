import re
from django.core.management.base import BaseCommand
from website.models import ContactSubmission

class Command(BaseCommand):
    help = 'Cleans up automatic mock/test contact submissions from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview records that will be deleted without actually deleting them',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all contact submissions from the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_all = options['all']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN MODE: No database changes will be saved.'))

        if delete_all:
            queryset = ContactSubmission.objects.all()
            self.stdout.write(f'Selected ALL contact submissions ({queryset.count()} records).')
        else:
            # We want to identify mock records based on common test generation patterns:
            # 1. Names that are single-word alphanumeric strings of length >= 10 (e.g. URstvHJTZAmdtq)
            # 2. Emails that contain 4 or more dots in the local part (e.g. e.l.m.xoo.x.0.01@gmail.com)
            # 3. Subjects that look like single-word alphanumeric strings of length >= 12
            
            all_submissions = ContactSubmission.objects.all()
            ids_to_delete = []

            # Patterns
            single_word_pattern = re.compile(r'^[A-Za-z0-9]{10,}$')
            
            for submission in all_submissions:
                is_mock = False
                
                # Check 1: Alphanumeric single-word name (length >= 10, no spaces)
                if single_word_pattern.match(submission.name or ''):
                    is_mock = True
                
                # Check 2: Email contains 4 or more dots in the username part
                email_parts = (submission.email or '').split('@')
                if len(email_parts) == 2:
                    local_part = email_parts[0]
                    if local_part.count('.') >= 4:
                        is_mock = True
                
                # Check 3: Alphanumeric single-word subject of length >= 12
                if single_word_pattern.match(submission.subject or '') and len(submission.subject or '') >= 12:
                    is_mock = True

                if is_mock:
                    ids_to_delete.append(submission.id)

            queryset = ContactSubmission.objects.filter(id__in=ids_to_delete)
            self.stdout.write(f'Selected mock contact submissions ({queryset.count()} records out of {all_submissions.count()} total).')

        if queryset.exists():
            for c in queryset[:20]:
                self.stdout.write(f'  - ID {c.id}: Name: {c.name} | Email: {c.email} | Subject: {c.subject}')
            if queryset.count() > 20:
                self.stdout.write(f'  - ... and {queryset.count() - 20} more records.')

            if not dry_run:
                count, _ = queryset.delete()
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} contact submissions.'))
            else:
                self.stdout.write(self.style.WARNING(f'Dry-run completed. Would have deleted {queryset.count()} records.'))
        else:
            self.stdout.write(self.style.SUCCESS('No matching contact submissions found.'))
