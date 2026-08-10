from django.db import models
from django.conf import settings

GHANA_REGIONS = [
    ('Greater Accra', 'Greater Accra'),
    ('Ashanti', 'Ashanti'),
    ('Eastern', 'Eastern'),
    ('Western', 'Western'),
    ('Central', 'Central'),
    ('Northern', 'Northern'),
    ('Upper East', 'Upper East'),
    ('Upper West', 'Upper West'),
    ('Volta', 'Volta'),
    ('Bono', 'Bono'),
    ('Bono East', 'Bono East'),
    ('Ahafo', 'Ahafo'),
    ('Oti', 'Oti'),
    ('Savannah', 'Savannah'),
    ('North East', 'North East'),
    ('Western North', 'Western North'),
]

class FarmerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='farmers/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='farmers/covers/', blank=True, null=True)
    phone = models.CharField(max_length=20)
    region = models.CharField(max_length=50, choices=GHANA_REGIONS)
    district = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farm_name} ({self.user.get_full_name() or self.user.username})"

class Payout(models.Model):
    class PayoutStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class PayoutMethod(models.TextChoices):
        MTN_MOMO = 'MTN_MOMO', 'MTN Mobile Money'
        TELECEL_CASH = 'TELECEL_CASH', 'Telecel Cash'
        AIRTELTIGO_MONEY = 'AIRTELTIGO_MONEY', 'AirtelTigo Money'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Account'

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PayoutMethod.choices)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=150, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True, help_text="Required for bank transfer")
    reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payout {self.id} - {self.farmer.farm_name} - GHS {self.amount}"

class FarmerNotificationSetting(models.Model):
    farmer = models.OneToOneField(FarmerProfile, on_delete=models.CASCADE, related_name='notification_settings')
    new_order = models.BooleanField(default=True)
    order_status = models.BooleanField(default=True)
    new_message = models.BooleanField(default=True)
    new_review = models.BooleanField(default=True)
    payout = models.BooleanField(default=True)
    promotions = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification settings for {self.farmer.farm_name}"
