from decimal import Decimal
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from admin_panel.models import SiteSettings, Promotion, SupportTicket, SupportTicketMessage, ActivityLog
from farmers.models import FarmerProfile
from products.models import Product

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds database with demo administrator records, tickets, and configurations."

    def handle(self, *args, **options):
        self.stdout.write("Starting admin database seeding...")

        # 1. Create Superuser admin operator
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@agroconnect.com",
                "first_name": "Kofi",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True
            }
        )
        if created or not admin_user.check_password("admin1234"):
            admin_user.set_password("admin1234")
            admin_user.save()
        self.stdout.write(f"Admin operator 'admin' (password: admin1234) ready.")

        # 2. Create global SiteSettings configuration
        settings_obj, created = SiteSettings.objects.get_or_create(
            id=1,
            defaults={
                "site_name": "AgroConnect",
                "site_email": "info@agroconnect.com",
                "site_phone": "+233 24 123 4567",
                "currency": "GHS",
                "timezone": "Africa/Accra",
                "commission_rate": Decimal("10.00"),
                "momo_api_url": "https://api.mtn.com.gh/momo/v1/",
                "seo_title": "AgroConnect - Ghana's Crop Marketplace",
                "seo_keywords": "agriculture, farm fresh, organic yam, ghana crop market",
                "seo_description": "Buy organic crops direct from Ghanaian growers."
            }
        )
        self.stdout.write("Global SiteSettings initialized.")

        # 3. Create promotions campaigns
        p1, _ = Promotion.objects.get_or_create(
            title="Veggie Fest Discounts",
            defaults={
                "description": "Harvest season vegetables discounts up to 15% off. Get fresh organic cabbage, carrots, and sweet bell peppers.",
                "discount_percentage": Decimal("15.00"),
                "start_date": timezone.now(),
                "end_date": timezone.now() + datetime.timedelta(days=14),
                "is_active": True
            }
        )
        p2, _ = Promotion.objects.get_or_create(
            title="Yam and Tubers Campaign",
            defaults={
                "description": "Bulk purchases on yams and cassava. Support local growers directly in Eastern Region.",
                "discount_percentage": Decimal("10.00"),
                "start_date": timezone.now() - datetime.timedelta(days=2),
                "end_date": timezone.now() + datetime.timedelta(days=10),
                "is_active": True
            }
        )
        self.stdout.write("Promotions campaigns seeded.")

        # 4. Create Support tickets
        grower_user = User.objects.filter(username="grower").first()
        mary_user = User.objects.filter(username="mary").first()
        
        if grower_user:
            t1, _ = SupportTicket.objects.get_or_create(
                user=grower_user,
                subject="Payout request verification issue",
                defaults={
                    "category": "Billing",
                    "priority": "HIGH",
                    "status": "OPEN"
                }
            )
            # Add message log
            SupportTicketMessage.objects.get_or_create(
                ticket=t1,
                sender=grower_user,
                defaults={
                    "message": "I submitted a payout withdrawal request to MTN MoMo 2 days ago but it is still showing pending status. Please assist."
                }
            )
            
        if mary_user:
            t2, _ = SupportTicket.objects.get_or_create(
                user=mary_user,
                subject="Order refund for cancelled tomatoes",
                defaults={
                    "category": "Shipping",
                    "priority": "MEDIUM",
                    "status": "RESOLVED"
                }
            )
            # Add message log
            m1, _ = SupportTicketMessage.objects.get_or_create(
                ticket=t2,
                sender=mary_user,
                defaults={
                    "message": "The tomatoes order was rejected by the grower Kofi Mensah. How long will the refund take to show in my mobile wallet?"
                }
            )
            SupportTicketMessage.objects.get_or_create(
                ticket=t2,
                sender=admin_user,
                defaults={
                    "message": "Hello Mary, the refund has been processed back to your mobile money number. It should reflect in 5-10 minutes. Thank you!"
                }
            )
            
        self.stdout.write("Support tickets seeded.")

        # 5. Create Activity logs
        ActivityLog.objects.get_or_create(
            admin=admin_user,
            action="Approved Payout request ID 1 for GHS 120.00",
            defaults={"ip_address": "192.168.1.10"}
        )
        ActivityLog.objects.get_or_create(
            admin=admin_user,
            action="Verified farmer Kofi's Green Acres Farm profile",
            defaults={"ip_address": "192.168.1.10"}
        )
        ActivityLog.objects.get_or_create(
            admin=admin_user,
            action="Added Vegetables and Fruits marketplace categories",
            defaults={"ip_address": "127.0.0.1"}
        )
        self.stdout.write("Activity audit logs ready.")

        self.stdout.write("Admin database seeding completed successfully!")
