from django.db import models
from django.conf import settings

class PaymentMethod(models.Model):
    class PaymentTypeChoices(models.TextChoices):
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
        CARD = 'CARD', 'Card'

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PaymentTypeChoices.choices, default=PaymentTypeChoices.MOBILE_MONEY)
    provider = models.CharField(max_length=50, help_text="e.g. MTN, Telecel, Visa, Mastercard")
    masked_reference = models.CharField(max_length=50, help_text="e.g. **** 4342 or +233 24 **** 123")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} ({self.masked_reference}) for {self.buyer.username}"
