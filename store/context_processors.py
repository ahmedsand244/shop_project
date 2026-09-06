from django.core.cache import cache
from .models import Category, WishlistItem, UserProfile, SiteAnnouncement, Order


def store_context(request):
    """
    Global context processor to provide cart counter, wishlist counter,
    categories, user profile status, and support links to all templates.
    Optimized for high-speed caching and minimal database hits.
    """
    try:
        Order.current_base_url = request.build_absolute_uri('/')[:-1]
    except Exception:
        pass

    cart = request.session.get('cart', {})
    cart_total_items = 0
    if isinstance(cart, dict):
        cart_total_items = sum(v for v in cart.values() if isinstance(v, int))

    wishlist_count = 0
    wishlist_product_ids = []
    user_profile = None
    show_onboarding = False

    if request.user.is_authenticated:
        wishlist_product_ids = list(
            WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
        wishlist_count = len(wishlist_product_ids)

        user_profile = getattr(request.user, 'profile', None)
        if user_profile is None:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                user_profile = UserProfile.objects.create(user=request.user)

        if not user_profile.is_complete():
            show_onboarding = True

    # Use 60s in-memory cached queries for sitewide elements
    categories = cache.get('global_categories')
    if categories is None:
        categories = list(Category.objects.all().order_by('order'))
        cache.set('global_categories', categories, 60)

    site_announcement = cache.get('site_announcement')
    if site_announcement is None:
        site_announcement = SiteAnnouncement.objects.filter(is_active=True).first()
        cache.set('site_announcement', site_announcement, 60)

    return {
        'cart_total_items': cart_total_items,
        'wishlist_count': wishlist_count,
        'wishlist_product_ids': wishlist_product_ids,
        'global_categories': categories,
        'user_profile': user_profile,
        'show_onboarding': show_onboarding,
        'support_phone': '01011079572',
        'support_whatsapp_url': 'https://wa.me/201011079572?text=Hello%20NEXUS%20STORE%20Support%2C%20I%20would%20like%20assistance.',
        'site_announcement': site_announcement,
    }

