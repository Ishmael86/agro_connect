from accounts.models import Wishlist


def wishlist_context(request):
    """Inject the set of wishlisted product IDs for the current user."""
    if request.user.is_authenticated and request.user.account_type == 'BUYER':
        ids = set(
            Wishlist.objects.filter(buyer=request.user).values_list('product_id', flat=True)
        )
        return {'user_wishlist_ids': ids}
    return {'user_wishlist_ids': set()}
