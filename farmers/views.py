from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import FarmerProfile, GHANA_REGIONS

def farmer_list_view(request):
    farmers_list = FarmerProfile.objects.all().select_related('user').order_by('-verified', '-rating')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        farmers_list = farmers_list.filter(
            Q(farm_name__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Location (Region) Filter
    region_filter = request.GET.get('region', '')
    if region_filter:
        farmers_list = farmers_list.filter(region=region_filter)

    # Pagination
    paginator = Paginator(farmers_list, 8) # 8 farmers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'regions': GHANA_REGIONS,
        'search_query': search_query,
        'selected_region': region_filter,
        'breadcrumbs': [('Farmers', '/farmers/')],
    }
    return render(request, 'marketplace/farmer_list.html', context)

def farmer_detail_view(request, id):
    farmer = get_object_or_404(FarmerProfile.objects.select_related('user'), id=id)
    # Get products for this farmer
    products = farmer.products.filter(is_available=True)
    
    context = {
        'farmer': farmer,
        'products': products,
    }
    return render(request, 'marketplace/farmer_detail.html', context)
