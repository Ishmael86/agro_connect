from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from .models import Category, Product, ContactMessage
from .forms import ContactForm
from farmers.models import FarmerProfile, GHANA_REGIONS

User = get_user_model()

# Static Testimonials data
TESTIMONIALS = [
    {
        'name': 'Kofi Mensah',
        'role': 'Restaurant Owner, Accra',
        'rating': 5,
        'review': 'AgroConnect has transformed my restaurant sourcing. I get fresh plantain and vegetables directly from farms in the Eastern region. Extremely reliable and fresh!',
        'avatar': 'kofi.jpg'
    },
    {
        'name': 'Ama Serwaa',
        'role': 'Fruit Vendor, Kumasi',
        'rating': 5,
        'review': 'Finding high-quality pineapples and papayas used to take days of travel. Now I can connect with certified farmers in seconds. Safe delivery is a lifesaver!',
        'avatar': 'ama.jpg'
    },
    {
        'name': 'Emmanuel Boateng',
        'role': 'Local Farmer, Sunyani',
        'rating': 5,
        'review': 'Before joining AgroConnect, I lost a third of my cabbage harvests because I could not find buyers in time. Now I sell directly to wholesalers in Accra before harvesting.',
        'avatar': 'emmanuel.jpg'
    },
    {
        'name': 'Yaa Asantewaa',
        'role': 'Household Buyer, Tema',
        'rating': 4,
        'review': 'The prices are very competitive and the quality of grains and tubers is exceptional. The mobile money payment option is so easy to use.',
        'avatar': 'yaa.jpg'
    }
]

def home_view(request):
    featured_products = Product.objects.filter(is_featured=True, is_available=True).select_related('farmer', 'farmer__user')[:6]
    categories = Category.objects.annotate(product_count=Count('products'))[:8] # Show up to 8 categories

    # Dynamic Statistics calculations from DB with realistic baselines
    farmers_count = FarmerProfile.objects.count() + 2500
    buyers_count = User.objects.filter(account_type='BUYER').count() + 15000
    products_count = Product.objects.count() + 1200
    communities_count = 50

    context = {
        'featured_products': featured_products,
        'categories': categories,
        'farmers_count': f"{farmers_count:,}+",
        'buyers_count': f"{buyers_count:,}+",
        'products_count': f"{products_count:,}+",
        'communities_count': f"{communities_count}+",
        'testimonials': TESTIMONIALS[:4],
    }
    return render(request, 'core/home.html', context)

def product_list_view(request):
    products_query = Product.objects.filter(is_available=True).select_related('farmer', 'farmer__user', 'category')
    categories = Category.objects.annotate(product_count=Count('products'))
    
    # Filtering parameters
    category_slug = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    region_filter = request.GET.get('region', '')
    rating_filter = request.GET.get('rating', '')
    availability = request.GET.get('availability', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'newest')

    # Apply search filter
    if search_query:
        products_query = products_query.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(farmer__farm_name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Apply category filter
    if category_slug:
        products_query = products_query.filter(category__slug=category_slug)

    # Apply price filters
    if min_price:
        try:
            products_query = products_query.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products_query = products_query.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Apply region filter
    if region_filter:
        products_query = products_query.filter(farmer__region=region_filter)

    # Apply rating filter
    if rating_filter:
        try:
            products_query = products_query.filter(rating__gte=float(rating_filter))
        except ValueError:
            pass

    # Apply availability filter
    if availability == 'in_stock':
        products_query = products_query.filter(stock_quantity__gt=0)

    # Sorting
    if sort_by == 'price_low':
        products_query = products_query.order_by('price')
    elif sort_by == 'price_high':
        products_query = products_query.order_by('-price')
    elif sort_by == 'rating':
        products_query = products_query.order_by('-rating')
    elif sort_by == 'popular':
        products_query = products_query.order_by('-review_count')
    else: # newest
        products_query = products_query.order_by('-created_at')

    # Pagination
    paginator = Paginator(products_query, 16) # 16 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Active filters context
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)

    # Setup breadcrumbs
    breadcrumbs = [('Products', '/products/')]
    if active_category:
        breadcrumbs.append((active_category.name, f"/products/?category={category_slug}"))

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'regions': GHANA_REGIONS,
        'search_query': search_query,
        'selected_category': category_slug,
        'active_category': active_category,
        'min_price': min_price,
        'max_price': max_price,
        'selected_region': region_filter,
        'selected_rating': rating_filter,
        'selected_availability': availability,
        'selected_sort': sort_by,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'marketplace/product_list.html', context)

def product_detail_view(request, slug):
    product = get_object_or_404(Product.objects.select_related('farmer', 'farmer__user', 'category'), slug=slug)
    # Related products from same category, excluding current product
    related_products = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'marketplace/product_detail.html', context)

def category_list_view(request):
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    context = {
        'categories': categories,
        'breadcrumbs': [('Categories', '/categories/')]
    }
    return render(request, 'marketplace/category_list.html', context)

def about_view(request):
    context = {
        'breadcrumbs': [('About Us', '/about/')]
    }
    return render(request, 'core/about.html', context)

def how_it_works_view(request):
    context = {
        'breadcrumbs': [('How It Works', '/how-it-works/')]
    }
    return render(request, 'core/how_it_works.html', context)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully. We will get back to you soon!")
            return redirect('contact')
        else:
            messages.error(request, "Please check the form inputs and try again.")
    else:
        form = ContactForm()
    
    context = {
        'form': form,
        'breadcrumbs': [('Contact Us', '/contact/')]
    }
    return render(request, 'core/contact.html', context)

def search_view(request):
    query = request.GET.get('q', '')
    products = []
    farmers = []
    categories = []

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).select_related('farmer', 'farmer__user')[:6]

        farmers = FarmerProfile.objects.filter(
            Q(farm_name__icontains=query) |
            Q(description__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )[:6]

        categories = Category.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:6]

    context = {
        'query': query,
        'products': products,
        'farmers': farmers,
        'categories': categories,
    }
    return render(request, 'core/search_results.html', context)
