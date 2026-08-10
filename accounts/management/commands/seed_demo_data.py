import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

from accounts.models import BuyerProfile, Wishlist, Address, Conversation, Message
from payments.models import PaymentMethod
from products.models import Product, Review
from notifications.models import Notification
from orders.models import Order, OrderItem
from farmers.models import FarmerProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds database with realistic buyer demo data for mary'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding buyer demo data...')
        
        try:
            with transaction.atomic():
                # 1. Create or get Buyer user 'mary'
                buyer_user, created = User.objects.get_or_create(
                    username='mary',
                    defaults={
                        'email': 'mary@agroconnect.com.gh',
                        'first_name': 'Mary',
                        'last_name': 'Mensah',
                        'phone': '+233241234567',
                        'account_type': 'BUYER'
                    }
                )
                if created:
                    buyer_user.set_password('marypass')
                    buyer_user.save()
                    self.stdout.write(self.style.SUCCESS('Buyer user created: mary / marypass'))
                else:
                    self.stdout.write('Buyer user "mary" already exists.')
                
                # 2. Ensure BuyerProfile exists
                profile, p_created = BuyerProfile.objects.get_or_create(
                    user=buyer_user,
                    defaults={
                        'phone': '+233241234567',
                        'reward_points': 320
                    }
                )
                self.stdout.write('BuyerProfile created/verified.')

                # 3. Create Addresses
                Address.objects.filter(buyer=buyer_user).delete()
                addr1 = Address.objects.create(
                    buyer=buyer_user,
                    label='Home',
                    full_name='Mary Mensah',
                    phone='+233241234567',
                    region='Greater Accra',
                    city='Adenta',
                    address='House 12, Adenta Street, near the local market',
                    additional_information='Leave at the front gate.',
                    is_default=True
                )
                addr2 = Address.objects.create(
                    buyer=buyer_user,
                    label='Work',
                    full_name='Mary Mensah',
                    phone='+233249876543',
                    region='Greater Accra',
                    city='East Legon',
                    address='Accra Mall Office Block, Floor 2 Suite B',
                    additional_information='Deliver to reception desk.',
                    is_default=False
                )
                self.stdout.write(self.style.SUCCESS('Seeded 2 delivery addresses.'))

                # 4. Create Payment Methods
                PaymentMethod.objects.filter(buyer=buyer_user).delete()
                pm1 = PaymentMethod.objects.create(
                    buyer=buyer_user,
                    payment_type='MOBILE_MONEY',
                    provider='MTN MoMo',
                    masked_reference='+233 24 **** 567',
                    is_default=True
                )
                pm2 = PaymentMethod.objects.create(
                    buyer=buyer_user,
                    payment_type='CARD',
                    provider='Visa Card',
                    masked_reference='Visa ending in 4342',
                    is_default=False
                )
                pm3 = PaymentMethod.objects.create(
                    buyer=buyer_user,
                    payment_type='CARD',
                    provider='Mastercard',
                    masked_reference='Mastercard ending in 8888',
                    is_default=False
                )
                self.stdout.write(self.style.SUCCESS('Seeded 3 payment methods.'))

                # 5. Populate Wishlist
                Wishlist.objects.filter(buyer=buyer_user).delete()
                products = list(Product.objects.filter(is_available=True))
                if len(products) >= 4:
                    # Wishlist sweet items
                    for prod in products[:4]:
                        Wishlist.objects.create(buyer=buyer_user, product=prod)
                    self.stdout.write(self.style.SUCCESS('Added 4 items to wishlist.'))

                # 6. Populate Orders & OrderItems
                Order.objects.filter(user=buyer_user).delete()
                farmers = list(FarmerProfile.objects.all())
                
                if len(products) >= 6 and len(farmers) >= 2:
                    # Let's seed 1 delivered order (so we can review it)
                    ord1_num = f"AGC-2026-{uuid.uuid4().hex[:6].upper()}"
                    ord1 = Order.objects.create(
                        user=buyer_user,
                        order_number=ord1_num,
                        full_name='Mary Mensah',
                        phone='+233241234567',
                        delivery_address=addr1.address,
                        region=addr1.region,
                        city=addr1.city,
                        payment_method='MOBILE_MONEY',
                        subtotal=Decimal('60.00'),
                        delivery_fee=Decimal('10.00'),
                        total=Decimal('70.00'),
                        status='DELIVERED'
                    )
                    # Force dates back to simulate history
                    ord1.created_at = datetime.now() - timedelta(days=5)
                    ord1.save()
                    
                    OrderItem.objects.create(
                        order=ord1,
                        product=products[0],
                        farmer=products[0].farmer,
                        quantity=2,
                        unit_price=products[0].final_price,
                        subtotal=products[0].final_price * 2
                    )
                    OrderItem.objects.create(
                        order=ord1,
                        product=products[1],
                        farmer=products[1].farmer,
                        quantity=1,
                        unit_price=products[1].final_price,
                        subtotal=products[1].final_price
                    )

                    # Seed 1 processing order
                    ord2_num = f"AGC-2026-{uuid.uuid4().hex[:6].upper()}"
                    ord2 = Order.objects.create(
                        user=buyer_user,
                        order_number=ord2_num,
                        full_name='Mary Mensah',
                        phone='+233241234567',
                        delivery_address=addr1.address,
                        region=addr1.region,
                        city=addr1.city,
                        payment_method='CARD_PAYMENT',
                        subtotal=Decimal('175.00'),
                        delivery_fee=Decimal('10.00'),
                        total=Decimal('185.00'),
                        status='PROCESSING'
                    )
                    OrderItem.objects.create(
                        order=ord2,
                        product=products[2],
                        farmer=products[2].farmer,
                        quantity=3,
                        unit_price=products[2].final_price,
                        subtotal=products[2].final_price * 3
                    )

                    # Seed 1 shipped order
                    ord3_num = f"AGC-2026-{uuid.uuid4().hex[:6].upper()}"
                    ord3 = Order.objects.create(
                        user=buyer_user,
                        order_number=ord3_num,
                        full_name='Mary Mensah',
                        phone='+233241234567',
                        delivery_address=addr1.address,
                        region=addr1.region,
                        city=addr1.city,
                        payment_method='MOBILE_MONEY',
                        subtotal=Decimal('310.00'),
                        delivery_fee=Decimal('0.00'),
                        total=Decimal('310.00'),
                        status='SHIPPED'
                    )
                    OrderItem.objects.create(
                        order=ord3,
                        product=products[3],
                        farmer=products[3].farmer,
                        quantity=5,
                        unit_price=products[3].final_price,
                        subtotal=products[3].final_price * 5
                    )
                    
                    self.stdout.write(self.style.SUCCESS('Seeded 3 orders (Delivered, Processing, Shipped).'))

                # 7. Create Reviews
                Review.objects.filter(buyer=buyer_user).delete()
                if len(products) >= 2:
                    Review.objects.create(
                        buyer=buyer_user,
                        product=products[0],
                        rating=5,
                        comment='Super fresh and organic. Highly recommended!'
                    )
                    Review.objects.create(
                        buyer=buyer_user,
                        product=products[1],
                        rating=4,
                        comment='Good quality, fast delivery.'
                    )
                    self.stdout.write(self.style.SUCCESS('Seeded 2 product reviews.'))

                # 8. Create Messages & Threads
                Conversation.objects.filter(buyer=buyer_user).delete()
                if len(farmers) >= 2:
                    # Conv 1
                    c1 = Conversation.objects.create(buyer=buyer_user, farmer=farmers[0])
                    Message.objects.create(
                        conversation=c1,
                        sender=farmers[0].user,
                        message="Hello Mary, thank you for your recent purchase! Your tomatoes are freshly harvested and will be delivered shortly."
                    )
                    Message.objects.create(
                        conversation=c1,
                        sender=buyer_user,
                        message="Thank you! Looking forward to it."
                    )
                    # Conv 2
                    c2 = Conversation.objects.create(buyer=buyer_user, farmer=farmers[1])
                    Message.objects.create(
                        conversation=c2,
                        sender=buyer_user,
                        message="Do you have sweet potatoes in stock?"
                    )
                    Message.objects.create(
                        conversation=c2,
                        sender=farmers[1].user,
                        message="Yes Mary, fresh sweet potatoes were harvested yesterday. How many bags do you need?"
                    )
                    self.stdout.write(self.style.SUCCESS('Seeded 2 direct message conversations.'))

                # 9. Create Notifications
                Notification.objects.filter(buyer=buyer_user).delete()
                Notification.objects.create(
                    buyer=buyer_user,
                    title='Order Delivered 🎉',
                    message='Your order #AGC-2026-F6D2 has been delivered. Please rate the products.',
                    notification_type='ORDER_UPDATE',
                    is_read=True
                )
                Notification.objects.create(
                    buyer=buyer_user,
                    title='Order Shipped 🚚',
                    message='Your order #AGC-2026-A109 has been shipped and is on its way.',
                    notification_type='ORDER_UPDATE',
                    is_read=False
                )
                Notification.objects.create(
                    buyer=buyer_user,
                    title='New Message received 💬',
                    message='Green Fields Farm sent you a message.',
                    notification_type='MESSAGE',
                    is_read=False
                )
                Notification.objects.create(
                    buyer=buyer_user,
                    title='Unlock Free Delivery! 📦',
                    message='Spend GHS 300.00 or more to enjoy free delivery from any verified farmer.',
                    notification_type='PROMOTION',
                    is_read=False
                )
                self.stdout.write(self.style.SUCCESS('Seeded 4 notifications (1 read, 3 unread).'))

                self.stdout.write(self.style.SUCCESS('Buyer demo seeding completed successfully!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to seed: {str(e)}'))
