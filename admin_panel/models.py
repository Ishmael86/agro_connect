from django.db import models
from django.conf import settings

class ActivityLog(models.Model):
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_activity_logs')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.action} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class SupportTicket(models.Model):
    class StatusChoices(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        WAITING = 'WAITING', 'Waiting'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    class PriorityChoices(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=100)  # e.g., "Billing", "Shipping", "Quality"
    priority = models.CharField(max_length=15, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)
    status = models.CharField(max_length=15, choices=StatusChoices.choices, default=StatusChoices.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.get_status_display()})"

class SupportTicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in Ticket #{self.ticket.id}"

class Promotion(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='promotions/', blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class SiteSettings(models.Model):
    # General Settings
    site_name = models.CharField(max_length=100, default="AgroConnect")
    site_email = models.EmailField(default="info@agroconnect.com")
    site_phone = models.CharField(max_length=50, default="+233 24 123 4567")
    currency = models.CharField(max_length=10, default="GHS")
    timezone = models.CharField(max_length=50, default="Africa/Accra")
    site_description = models.TextField(default="Connecting farmers directly with buyers in Ghana.")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00) # Percentage commission
    maintenance_mode = models.BooleanField(default=False)
    
    # Payment Settings
    momo_api_url = models.CharField(max_length=255, blank=True, null=True)
    bank_transfer_enabled = models.BooleanField(default=True)
    
    # Email Settings
    smtp_host = models.CharField(max_length=150, default="smtp.mailgun.org")
    smtp_port = models.IntegerField(default=587)
    smtp_user = models.CharField(max_length=150, blank=True, null=True)
    smtp_password = models.CharField(max_length=150, blank=True, null=True)
    
    # SMS Settings
    sms_api_key = models.CharField(max_length=255, blank=True, null=True)
    sms_sender_id = models.CharField(max_length=50, default="AgroConnect")
    
    # SEO Settings
    seo_title = models.CharField(max_length=200, default="AgroConnect - Ghana's Organic Marketplace")
    seo_keywords = models.CharField(max_length=255, default="agriculture, farm, fresh vegetables, ghana crops")
    seo_description = models.TextField(default="Buy fresh farm crop produce directly from organic local growers in Ghana.")

    def __str__(self):
        return "Global Site Settings"
