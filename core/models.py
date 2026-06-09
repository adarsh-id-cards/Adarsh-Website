from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models

def office_work_shared_file_upload_to(instance, filename):
    """Fallback for legacy migrations."""
    return f"temp/{filename}"

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('operator', 'Operator'),
    ]
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator', db_index=True)
    welcome_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.role == 'admin' or self.is_superuser:
            self.is_staff = True
            self.is_superuser = True
        else:
            # Operators are staff but not superusers
            self.is_staff = True
            self.is_superuser = False
            
        super().save(*args, **kwargs)

class WebsiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default='Adarsh ID Cards')
    site_logo = models.ImageField(upload_to='site/', blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    about_text = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_value(cls, key, default=''):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description=None):
        obj, created = cls.objects.update_or_create(key=key, defaults={'value': value})
        if description:
            obj.description = description
            obj.save()
        return obj

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Logged in'),
        ('logout', 'Logged out'),
        ('password_reset', 'Password reset'),
        ('website_update', 'Website update'),
        ('settings_update', 'Settings update'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    description = models.CharField(max_length=500)
    target_model = models.CharField(max_length=50, blank=True, default='')
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_name = models.CharField(max_length=200, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def icon_class(self):
        icons = {'login': 'fa-right-to-bracket', 'logout': 'fa-right-from-bracket', 'password_reset': 'fa-key', 'website_update': 'fa-globe', 'settings_update': 'fa-gear'}
        return icons.get(self.action, 'fa-circle-info')

    @property
    def icon_color(self):
        colors = {'login': 'verify', 'logout': 'edit', 'password_reset': 'approve', 'website_update': 'edit', 'settings_update': 'edit'}
        return colors.get(self.action, 'edit')

class EmailLog(models.Model):
    EMAIL_TYPE_WELCOME = 'welcome'
    EMAIL_TYPE_TEMP_PASSWORD = 'temp_password'
    EMAIL_TYPE_PASSWORD_CHANGE = 'password_change'
    EMAIL_TYPE_OTP_RESET = 'otp_reset'
    EMAIL_TYPE_SYSTEM = 'system'

    EMAIL_TYPE_CHOICES = [
        (EMAIL_TYPE_WELCOME, 'Welcome / Activation'),
        (EMAIL_TYPE_TEMP_PASSWORD, 'Temp Password'),
        (EMAIL_TYPE_PASSWORD_CHANGE, 'Password Change Notice'),
        (EMAIL_TYPE_OTP_RESET, 'Password Reset OTP'),
        (EMAIL_TYPE_SYSTEM, 'System / Custom'),
    ]

    STATUS_ON_HOLD = 'on_hold'
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    ]

    recipient_name = models.CharField(max_length=200, blank=True, default='')
    recipient_email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=300, blank=True, default='')
    body_text = models.TextField(blank=True, default='')
    body_html = models.TextField(blank=True, default='')
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES, default=EMAIL_TYPE_SYSTEM, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    error_message = models.TextField(blank=True, default='')
    sent_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient_email}: {self.subject} ({self.status})"
