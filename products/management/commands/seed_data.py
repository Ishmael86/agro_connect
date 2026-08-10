import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import User
from farmers.models import FarmerProfile
from products.models import Category, Product

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with categories, farmers, and products'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        try:
            with transaction.atomic():
                # 1. Create Superuser if not exists
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser(
                        username='admin',
                        email='admin@agroconnect.com.gh',
                        password='adminpass',
                        phone='+233541234567',
                        account_type='BUYER'
                    )
                    self.stdout.write(self.style.SUCCESS('Superuser created: admin / adminpass'))

                # 2. Create Categories
                categories_data = [
                    ('Fruits', 'fruits', 'Fresh and sweet seasonal fruits direct from orchard owners.'),
                    ('Vegetables', 'vegetables', 'Organic vegetables including leafy greens, onions, and tomatoes.'),
                    ('Grains & Cereals', 'grains-cereals', 'Dried grains, cereals, white maize, and rice bags.'),
                    ('Tubers', 'tubers', 'Freshly dug tubers including yam, cassava, and sweet potatoes.'),
                    ('Legumes', 'legumes', 'Protein-rich beans, groundnuts, and cowpea varieties.'),
                    ('Herbs & Spices', 'herbs-spices', 'Organic ginger, garlic, chili pepper, and local herbs.'),
                    ('Dairy & Eggs', 'dairy-eggs', 'Fresh farm eggs, local cheese, and dairy products.'),
                    ('Meat & Poultry', 'meat-poultry', 'Locally raised livestock, chicken, and meats.'),
                    ('Seeds & Inputs', 'seeds-inputs', 'High yield seeds, organic fertilizers, and farming inputs.'),
                    ('Processed Foods', 'processed-foods', 'Gari, palm oil, coconut oil, and other processed items.')
                ]
                
                categories = {}
                for name, slug, desc in categories_data:
                    cat, created = Category.objects.get_or_create(
                        slug=slug,
                        defaults={'name': name, 'description': desc}
                    )
                    categories[slug] = cat
                    
                self.stdout.write(self.style.SUCCESS(f'Seeded {len(categories)} categories.'))

                # 3. Create Farmers (Users + FarmerProfiles)
                farmers_data = [
                    ('kofi', 'Kofi', 'Mensah', 'Green Fields Farm', 'Eastern', 'Suhum', '+233241112222', 'We grow quality produce with care and deliver freshness.'),
                    ('kwame', 'Kwame', 'Nkrumah', 'Sunyani Gold Farm', 'Bono', 'Sunyani', '+233242223333', 'Specialized in sweet pineapples, papayas, and citrus fruits.'),
                    ('ama', 'Ama', 'Boateng', 'Ashanti Hills Farm', 'Ashanti', 'Mampong', '+233243334444', 'Sustainable farming focusing on yams, potatoes, and tubers.'),
                    ('yawo', 'Yawo', 'Agbodza', 'Volta Green Farm', 'Volta', 'Hohoe', '+233244445555', 'Fresh plantain and cassava straight from our fertile soils.'),
                    ('mustapha', 'Mustapha', 'Ali', 'Savannah Seeds & Inputs', 'Savannah', 'Damongo', '+233245556666', 'Supplying local farmers with high yield seeds and advice.'),
                    ('salomey', 'Salomey', 'Osei', 'Aburi Organic Gardens', 'Eastern', 'Aburi', '+233246667777', 'Fresh garden vegetables, organic carrots, and green peppers.'),
                    ('baba', 'Baba', 'Sule', 'Northern Grainers', 'Northern', 'Tamale', '+233247778888', 'Large scale supplier of maize, sorghum, and quality groundnuts.'),
                    ('abena', 'Abena', 'Dankwa', 'Kasoa Poultry & Egg', 'Central', 'Kasoa', '+233248889999', 'Fresh eggs and broiler chicken raised on organic feed.')
                ]

                farmer_profiles = []
                for username, first_name, last_name, farm_name, region, location, phone, desc in farmers_data:
                    # Create User
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': f'{username}@farmmail.com',
                            'first_name': first_name,
                            'last_name': last_name,
                            'phone': phone,
                            'account_type': 'FARMER'
                        }
                    )
                    if created:
                        user.set_password('farmpass')
                        user.save()
                    
                    # Create FarmerProfile
                    profile, p_created = FarmerProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'farm_name': farm_name,
                            'phone': phone,
                            'region': f'{region} Region' if 'Region' not in region else region,
                            'location': location,
                            'description': desc,
                            'verified': random.choice([True, True, False]), # High chance of being verified
                            'rating': random.choice([4.2, 4.5, 4.7, 4.8, 4.9])
                        }
                    )
                    farmer_profiles.append(profile)
                    
                self.stdout.write(self.style.SUCCESS(f'Seeded {len(farmer_profiles)} farmers.'))

                # 4. Create Products
                products_data = [
                    # name, category_slug, farmer_idx, price, unit, stock, location, is_featured, is_available
                    ('Fresh Tomatoes', 'vegetables', 0, 12.00, 'kg', 150, 'Suhum Market', True, True),
                    ('Sweet Pineapple', 'fruits', 1, 15.00, 'pc', 80, 'Sunyani Farm Gate', True, True),
                    ('Red Onions', 'vegetables', 5, 10.00, 'kg', 200, 'Aburi Gardens', True, True),
                    ('Yam Tubers (Pona)', 'tubers', 2, 8.00, 'kg', 300, 'Mampong Market', True, True),
                    ('Maize Grains', 'grains-cereals', 6, 8.00, 'kg', 500, 'Tamale Central', True, True),
                    ('Fresh Pepper (Habenero)', 'vegetables', 0, 20.00, 'kg', 100, 'Suhum Roadside', True, True),
                    ('Sweet Potatoes', 'tubers', 2, 6.00, 'kg', 120, 'Mampong Market', False, True),
                    ('Plantain Bunch (Apem)', 'tubers', 3, 6.00, 'bunch', 90, 'Hohoe Station', False, True),
                    ('Cabbage Head', 'vegetables', 5, 5.00, 'head', 110, 'Aburi Farms', False, True),
                    ('Organic Carrots', 'vegetables', 5, 6.00, 'bunch', 85, 'Aburi Farms', False, True),
                    ('Cowpea Beans', 'legumes', 6, 14.00, 'kg', 250, 'Tamale Central', False, True),
                    ('Premium Groundnuts', 'legumes', 6, 18.00, 'kg', 180, 'Tamale Central', False, True),
                    ('Cassava Roots', 'tubers', 3, 4.00, 'kg', 400, 'Hohoe Farm Gate', False, True),
                    ('Fresh Farm Eggs', 'dairy-eggs', 7, 45.00, 'crate', 60, 'Kasoa Coop', False, True),
                    ('Organic Ginger', 'herbs-spices', 5, 15.00, 'kg', 70, 'Aburi Gardens', False, True),
                    ('Dried Chili Pepper', 'herbs-spices', 0, 25.00, 'kg', 50, 'Suhum Market', False, True),
                    ('White Maize Seeds', 'seeds-inputs', 4, 30.00, 'bag', 40, 'Damongo Depot', False, True),
                    ('Organic Soybeans', 'legumes', 6, 12.00, 'kg', 350, 'Tamale Central', False, True),
                    ('Sweet Papaya', 'fruits', 1, 10.00, 'pc', 75, 'Sunyani Farm Gate', False, True),
                    ('Garden Eggs (African Eggplant)', 'vegetables', 0, 8.00, 'bag', 95, 'Suhum Market', False, True)
                ]

                products_seeded_count = 0
                for name, cat_slug, farmer_idx, price, unit, stock, location, is_featured, is_avail in products_data:
                    farmer = farmer_profiles[farmer_idx]
                    category = categories[cat_slug]
                    
                    product, created = Product.objects.get_or_create(
                        name=name,
                        farmer=farmer,
                        defaults={
                            'category': category,
                            'description': f"Naturally grown and freshly harvested {name} supplied directly from the fertile soils of {farmer.location}. We ensure strict environmental quality controls.",
                            'price': price,
                            'unit': unit,
                            'stock_quantity': stock,
                            'location': location,
                            'is_featured': is_featured,
                            'is_available': is_avail,
                            'rating': random.choice([4.2, 4.5, 4.7, 4.8, 4.9]),
                            'review_count': random.randint(15, 150)
                        }
                    )
                    if created:
                        products_seeded_count += 1
                        
                self.stdout.write(self.style.SUCCESS(f'Seeded {products_seeded_count} new products.'))
                self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to seed database: {str(e)}'))
