from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class AccountType(models.TextChoices):
        BUYER = 'BUYER', 'Buyer'
        FARMER = 'FARMER', 'Farmer'

    account_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
        default=AccountType.BUYER
    )
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_account_type_display()})"

from django.conf import settings
from farmers.models import GHANA_REGIONS

class BuyerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_profile')
    profile_image = models.ImageField(upload_to='buyers/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    reward_points = models.IntegerField(default=320)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Wishlist(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'product')

    def __str__(self):
        return f"{self.buyer.username} wants {self.product.name}"

class Address(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Home', help_text="e.g. Home, Office, Farm")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    region = models.CharField(max_length=50, choices=GHANA_REGIONS)
    city = models.CharField(max_length=100)
    address = models.TextField()
    additional_information = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} Address for {self.buyer.username}"

class Conversation(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    farmer = models.ForeignKey('farmers.FarmerProfile', on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer', 'farmer')

    def __str__(self):
        return f"Conversation: {self.buyer.username} & {self.farmer.farm_name}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in Thread {self.conversation.id}"
