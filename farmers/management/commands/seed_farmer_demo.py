from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

from farmers.models import FarmerProfile, Payout, FarmerNotificationSetting
from products.models import Product, Category, Review
from orders.models import Order, OrderItem
from accounts.models import Conversation, Message
from notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the database with realistic farmer dashboard demo records."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Create categories
        categories = ["Vegetables", "Fruits", "Grains", "Tubers"]
        cat_objs = {}
        for cat_name in categories:
            cat, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': f"Fresh agricultural {cat_name.lower()}"}
            )
            cat_objs[cat_name] = cat
        self.stdout.write("Categories seeded successfully.")

        # 2. Create Farmer User
        grower_user, created = User.objects.get_or_create(
            username="grower",
            defaults={
                "email": "grower@agroconnect.com",
                "first_name": "Kofi",
                "last_name": "Mensah",
                "account_type": "FARMER",
                "phone": "+233 24 987 6543"
            }
        )
        if created or not grower_user.check_password("farmer1234"):
            grower_user.set_password("farmer1234")
            grower_user.save()
        self.stdout.write(f"Farmer user 'grower' (password: farmer1234) ready.")

        # 3. Create FarmerProfile
        farmer_profile, _ = FarmerProfile.objects.get_or_create(
            user=grower_user,
            defaults={
                "farm_name": "Kofi's Green Acres Farm",
                "phone": "+233 24 987 6543",
                "region": "Ashanti",
                "district": "Kumasi Metropolitan",
                "location": "Kumasi Central Farm Area",
                "description": "Kofi's Green Acres is a certified organic farm specializing in fresh vegetables, organic grains, and premium tubers.",
                "verified": True,
                "rating": Decimal("4.8")
            }
        )
        self.stdout.write("FarmerProfile ready.")

        # 4. Create Notification Settings
        FarmerNotificationSetting.objects.get_or_create(farmer=farmer_profile)

        # 5. Create Buyer User
        buyer_user, created = User.objects.get_or_create(
            username="mary",
            defaults={
                "email": "mary@example.com",
                "first_name": "Mary",
                "last_name": "Annan",
                "account_type": "BUYER",
                "phone": "+233 55 123 4567"
            }
        )
        if created or not buyer_user.check_password("buyer1234"):
            buyer_user.set_password("buyer1234")
            buyer_user.save()
        self.stdout.write(f"Buyer user 'mary' (password: buyer1234) ready.")

        # 6. Create Products
        p1, _ = Product.objects.get_or_create(
            slug="kofis-fresh-tomatoes",
            defaults={
                "farmer": farmer_profile,
                "category": cat_objs["Vegetables"],
                "name": "Kofi's Fresh Tomatoes",
                "description": "Plump, sun-ripened organic red tomatoes harvested fresh daily.",
                "price": Decimal("25.00"),
                "unit": "kg",
                "stock_quantity": 80,
                "location": "Kumasi Central Market",
                "is_available": True
            }
        )
        
        p2, _ = Product.objects.get_or_create(
            slug="kofis-organic-rice",
            defaults={
                "farmer": farmer_profile,
                "category": cat_objs["Grains"],
                "name": "Kofi's Premium Organic Rice",
                "description": "Locally milled fragrant brown rice grown without synthetic pesticides.",
                "price": Decimal("65.00"),
                "unit": "bag",
                "stock_quantity": 35,
                "location": "Kumasi Central Market",
                "is_available": True
            }
        )

        p3, _ = Product.objects.get_or_create(
            slug="kofis-fresh-habanero-pepper",
            defaults={
                "farmer": farmer_profile,
                "category": cat_objs["Vegetables"],
                "name": "Kofi's Habanero Hot Peppers",
                "description": "Fiery hot fresh habanero peppers ideal for local sauces.",
                "price": Decimal("35.00"),
                "unit": "kg",
                "stock_quantity": 8,  # Low stock warning trigger!
                "location": "Kumasi Central Market",
                "is_available": True
            }
        )

        p4, _ = Product.objects.get_or_create(
            slug="kofis-white-yam-tubers",
            defaults={
                "farmer": farmer_profile,
                "category": cat_objs["Tubers"],
                "name": "Kofi's Sweet White Yams",
                "description": "Freshly dug large white yam tubers rich in fiber.",
                "price": Decimal("45.00"),
                "unit": "crate",
                "stock_quantity": 0,  # Out of stock warning trigger!
                "location": "Kumasi Central Market",
                "is_available": True
            }
        )
        self.stdout.write("Products created.")

        # 7. Create Orders
        # Order 1: Delivered (Completed transaction)
        o1, _ = Order.objects.get_or_create(
            order_number="ORD-88547",
            defaults={
                "user": buyer_user,
                "full_name": "Mary Annan",
                "phone": "+233 55 123 4567",
                "delivery_address": "House No 12, Ring Road East",
                "region": "Greater Accra",
                "city": "Accra",
                "subtotal": Decimal("575.00"),
                "delivery_fee": Decimal("10.00"),
                "total": Decimal("585.00"),
                "status": "DELIVERED",
                "payment_method": "MOBILE_MONEY"
            }
        )
        OrderItem.objects.get_or_create(
            order=o1, product=p1,
            defaults={
                "farmer": farmer_profile,
                "quantity": 10,
                "unit_price": Decimal("25.00"),
                "subtotal": Decimal("250.00")
            }
        )
        OrderItem.objects.get_or_create(
            order=o1, product=p2,
            defaults={
                "farmer": farmer_profile,
                "quantity": 5,
                "unit_price": Decimal("65.00"),
                "subtotal": Decimal("325.00")
            }
        )

        # Order 2: Pending (Action required)
        o2, _ = Order.objects.get_or_create(
            order_number="ORD-99543",
            defaults={
                "user": buyer_user,
                "full_name": "Mary Annan",
                "phone": "+233 55 123 4567",
                "delivery_address": "House No 12, Ring Road East",
                "region": "Greater Accra",
                "city": "Accra",
                "subtotal": Decimal("105.00"),
                "delivery_fee": Decimal("10.00"),
                "total": Decimal("115.00"),
                "status": "PENDING",
                "payment_method": "MOBILE_MONEY"
            }
        )
        OrderItem.objects.get_or_create(
            order=o2, product=p3,
            defaults={
                "farmer": farmer_profile,
                "quantity": 3,
                "unit_price": Decimal("35.00"),
                "subtotal": Decimal("105.00")
            }
        )

        # Order 3: Processing (In fulfillment)
        o3, _ = Order.objects.get_or_create(
            order_number="ORD-10142",
            defaults={
                "user": buyer_user,
                "full_name": "Mary Annan",
                "phone": "+233 55 123 4567",
                "delivery_address": "House No 12, Ring Road East",
                "region": "Greater Accra",
                "city": "Accra",
                "subtotal": Decimal("200.00"),
                "delivery_fee": Decimal("10.00"),
                "total": Decimal("210.00"),
                "status": "PROCESSING",
                "payment_method": "MOBILE_MONEY"
            }
        )
        OrderItem.objects.get_or_create(
            order=o3, product=p1,
            defaults={
                "farmer": farmer_profile,
                "quantity": 8,
                "unit_price": Decimal("25.00"),
                "subtotal": Decimal("200.00")
            }
        )
        self.stdout.write("Orders and items seeded.")

        # 8. Seed Payouts
        Payout.objects.get_or_create(
            reference="PAY-REF-9082",
            defaults={
                "farmer": farmer_profile,
                "amount": Decimal("150.00"),
                "payment_method": "MTN_MOMO",
                "account_number": "+233 24 987 6543",
                "account_name": "Kofi Mensah",
                "status": "COMPLETED",
                "processed_at": timezone.now() - datetime.timedelta(days=3)
            }
        )
        Payout.objects.get_or_create(
            reference="PAY-REF-1092",
            defaults={
                "farmer": farmer_profile,
                "amount": Decimal("50.00"),
                "payment_method": "MTN_MOMO",
                "account_number": "+233 24 987 6543",
                "account_name": "Kofi Mensah",
                "status": "PENDING"
            }
        )
        self.stdout.write("Payout entries ready.")

        # 9. Create Product Review
        Review.objects.get_or_create(
            buyer=buyer_user,
            product=p1,
            order=o1,
            defaults={
                "rating": 5,
                "comment": "Absolutely fresh and juicy tomatoes! Kofi packaging is neat and arrival was prompt."
            }
        )
        self.stdout.write("Reviews seeded.")

        # 10. Direct Messages Chat Thread
        conv, _ = Conversation.objects.get_or_create(buyer=buyer_user, farmer=farmer_profile)
        Message.objects.get_or_create(
            conversation=conv,
            sender=buyer_user,
            message="Hello Kofi, do you have any white yams in stock this week?",
            defaults={"created_at": timezone.now() - datetime.timedelta(hours=2)}
        )
        Message.objects.get_or_create(
            conversation=conv,
            sender=grower_user,
            message="Hi Mary! Yes, we have a fresh harvest of white yams coming in from our farm this Thursday.",
            defaults={"created_at": timezone.now() - datetime.timedelta(hours=1)}
        )
        Message.objects.get_or_create(
            conversation=conv,
            sender=buyer_user,
            message="Excellent, I will wait and place an order once the stock status updates. Thank you!",
            defaults={"created_at": timezone.now() - datetime.timedelta(minutes=30)}
        )
        self.stdout.write("Conversations and messages seeded.")

        # 11. Create Notifications
        Notification.objects.get_or_create(
            buyer=grower_user,
            title="New Order Alert: #ORD-99543",
            message="You have received a new pending order from Mary Annan containing 3 kg of Habanero Peppers.",
            defaults={"notification_type": "ORDER_UPDATE", "is_read": False}
        )
        
        Notification.objects.get_or_create(
            buyer=grower_user,
            title="Payout Request Processed",
            message="Your payout request PAY-REF-9082 of GHS 150.00 has been processed successfully.",
            defaults={"notification_type": "ORDER_UPDATE", "is_read": True}
        )
        self.stdout.write("Notifications ready.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
