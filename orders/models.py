from django.db import models
from django.conf import settings
from farmers.models import GHANA_REGIONS

class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class PaymentMethodChoices(models.TextChoices):
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
        CARD_PAYMENT = 'CARD_PAYMENT', 'Card Payment'
        CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', 'Cash on Delivery'

    class PaymentStatusChoices(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PAID = 'PAID', 'Paid'
        REFUNDED = 'REFUNDED', 'Refunded'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    region = models.CharField(max_length=50, choices=GHANA_REGIONS)
    city = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=30, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.MOBILE_MONEY)
    payment_status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.UNPAID)
    momo_provider = models.CharField(max_length=50, blank=True, null=True)
    momo_number = models.CharField(max_length=20, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_overall_status(self):
        """
        Recalculates and updates the overall order status based on individual item statuses.
        """
        items = self.items.all()
        if not items.exists():
            return
        statuses = set(items.values_list('status', flat=True))
        if statuses == {'DELIVERED'}:
            self.status = Order.StatusChoices.DELIVERED
        elif statuses == {'CANCELLED'}:
            self.status = Order.StatusChoices.CANCELLED
        elif 'SHIPPED' in statuses:
            self.status = Order.StatusChoices.SHIPPED
        elif 'PROCESSING' in statuses:
            self.status = Order.StatusChoices.PROCESSING
        elif 'PENDING' in statuses:
            self.status = Order.StatusChoices.PENDING
        self.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f"Order {self.order_number} ({self.full_name})"

class OrderItem(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    farmer = models.ForeignKey('farmers.FarmerProfile', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} (Order {self.order.order_number}) - {self.get_status_display()}"
