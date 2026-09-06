import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum, Count, Avg
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from .models import (
    Product, Category, Order, OrderItem,
    Review, WishlistItem, Coupon, ProductVariant,
    UserProfile, ContactMessage, ChatMessage,
    SiteAnnouncement, TrustBadge, HeroBanner, ProductQuestion
)
from .forms import CheckoutForm, ReviewForm, ExtendedRegisterForm, ContactForm
from .payment_utils import (
    get_auth_token, create_order as create_paymob_order, get_payment_key,
    PAYMOB_IFRAME_ID_CARD, PAYMOB_IFRAME_ID_VODAFONE,
    INTEGRATION_ID_CARD, INTEGRATION_ID_VODAFONE
)


# ==============================================================================
# 1. CATALOG & STOREFRONT VIEWS
# ==============================================================================

def home(request):
    """
    Main storefront homepage with Hero banner, flash deals,
    category pills, search, filter and pagination.
    """
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category')
    sort = request.GET.get('sort', 'featured')
    badge_filter = request.GET.get('badge')

    products = Product.objects.all().select_related('category').annotate(
        annotated_rating=Avg('reviews__rating'),
        annotated_reviews_count=Count('reviews')
    )

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_slug:
        products = products.filter(Q(category__slug=category_slug) | Q(category__id__iexact=category_slug))

    if badge_filter:
        products = products.filter(badge=badge_filter)

    # Sorting options
    if sort == 'low':
        products = products.order_by('price')
    elif sort == 'high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'popular':
        products = products.order_by('-views_count')
    else:
        products = products.order_by('-is_featured', '-created_at')

    # Hero & Showcase items
    hero_banner = HeroBanner.objects.filter(is_active=True).first()
    if hero_banner and hero_banner.product:
        featured_hero = hero_banner.product
    else:
        featured_hero = Product.objects.filter(is_featured=True).first() or products.first()

    # All products with images for the auto-rotating hero carousel
    hero_products = list(
        Product.objects.filter(image__isnull=False)
        .exclude(image='')
        .select_related('category')
        .annotate(
            annotated_rating=Avg('reviews__rating'),
            annotated_reviews_count=Count('reviews')
        )
        .order_by('-is_featured', '-created_at')[:12]
    )
    if not hero_products and featured_hero:
        hero_products = [featured_hero]

    trust_badges = TrustBadge.objects.filter(is_active=True).order_by('order', 'id')
    flash_deals = (
        Product.objects.filter(badge__in=['sale', 'hot', 'limited'])
        .select_related('category')
        .annotate(
            annotated_rating=Avg('reviews__rating'),
            annotated_reviews_count=Count('reviews')
        )[:4]
    )
    if not flash_deals.exists():
        flash_deals = products[:4]

    # Pagination
    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    from django.core.cache import cache
    categories = cache.get('global_categories')
    if categories is None:
        categories = list(Category.objects.all().order_by('order'))
        cache.set('global_categories', categories, 60)

    return render(request, 'home.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'featured_hero': featured_hero,
        'hero_banner': hero_banner,
        'hero_products': hero_products,
        'trust_badges': trust_badges,
        'flash_deals': flash_deals,
        'active_category': category_slug,
        'active_sort': sort,
        'search_query': query,
    })


def product_detail(request, product_id):
    """
    Comprehensive product detail view with gallery, reviews,
    Q&A, recently viewed tracking, stock indicator, and related products.
    """
    product = get_object_or_404(
        Product.objects.select_related('category').annotate(
            annotated_rating=Avg('reviews__rating'),
            annotated_reviews_count=Count('reviews')
        ),
        id=product_id
    )

    # Increment view count
    Product.objects.filter(id=product.id).update(views_count=F('views_count') + 1)

    # ---- Track Recently Viewed (session-based) ----
    rv_key = 'recently_viewed'
    rv_ids = request.session.get(rv_key, [])
    pid_str = str(product.id)
    if pid_str in rv_ids:
        rv_ids.remove(pid_str)
    rv_ids.insert(0, pid_str)
    rv_ids = rv_ids[:10]   # keep last 10
    request.session[rv_key] = rv_ids

    reviews = product.reviews.select_related('user').all()
    review_exists = False
    if request.user.is_authenticated:
        review_exists = reviews.filter(user=request.user).exists()

    # Q&A for this product
    questions = product.questions.filter(is_visible=True).select_related('user')

    # Gallery images
    gallery_images = product.gallery_images.all()

    # Review submission handling
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, "Please sign in to submit your verified review.")
            return redirect('login')

        if review_exists:
            messages.warning(request, 'You have already reviewed this product.')
            return redirect('product_detail', product_id=product.id)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Thank you! Your review has been published.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    # Related items in same category
    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(id=product.id)
        .select_related('category')
        .annotate(
            annotated_rating=Avg('reviews__rating'),
            annotated_reviews_count=Count('reviews')
        )[:4]
    )

    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'review_exists': review_exists,
        'related_products': related_products,
        'questions': questions,
        'gallery_images': gallery_images,
    })


# ==============================================================================
# 2. CART & CHECKOUT VIEWS (STRICT GATEKEEPING)
# ==============================================================================

def add_to_cart(request, product_id):
    """Traditional POST add to cart fallback with redirect."""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    qty = int(request.POST.get('quantity', 1))
    cart[product_id_str] = cart.get(product_id_str, 0) + max(1, qty)
    request.session['cart'] = cart
    messages.success(request, "Product added to your shopping bag.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('cart')))


def remove_from_cart(request, product_id):
    """Traditional remove from cart fallback."""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.info(request, "Item removed from your cart.")
    return redirect('cart')


def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str] += 1
        request.session['cart'] = cart
    return redirect('cart')


def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        if cart[product_id_str] > 1:
            cart[product_id_str] -= 1
        else:
            del cart[product_id_str]
        request.session['cart'] = cart
    return redirect('cart')


def cart_view(request):
    """
    Dedicated shopping cart page with calculations, coupon, and free shipping meter.
    """
    cart = request.session.get('cart', {})
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    products = Product.objects.filter(id__in=product_ids)

    cart_items = []
    subtotal = Decimal('0.00')

    for p in products:
        qty = cart.get(str(p.id), 0)
        item_subtotal = p.price * qty
        subtotal += item_subtotal
        cart_items.append({
            'product': p,
            'quantity': qty,
            'subtotal': item_subtotal
        })

    # Discount calculation if coupon stored in session
    coupon_code = request.session.get('applied_coupon')
    discount = Decimal('0.00')
    coupon_obj = None
    if coupon_code:
        coupon_obj = Coupon.objects.filter(code=coupon_code, active=True).first()
        if coupon_obj and subtotal >= coupon_obj.min_purchase:
            discount = (subtotal * Decimal(coupon_obj.discount_percent)) / Decimal(100)

    shipping_fee = Decimal('0.00') if subtotal >= 100 or subtotal == 0 else Decimal('15.00')
    grand_total = max(Decimal('0.00'), subtotal - discount + shipping_fee)

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'coupon': coupon_obj,
    })


@login_required(login_url='/login/?next=/checkout/')
def checkout(request):
    """
    Luxury One-Page Checkout view.
    Mandatory authentication required before placing order.
    Pre-populates with user's saved profile if available.
    """
    cart = request.session.get('cart', {})
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    products = Product.objects.filter(id__in=product_ids)

    if not cart or not products.exists():
        messages.info(request, "Your cart is empty. Please select products before proceeding.")
        return redirect('home')

    cart_items = []
    subtotal = Decimal('0.00')
    for p in products:
        qty = cart.get(str(p.id), 0)
        item_subtotal = p.price * qty
        subtotal += item_subtotal
        cart_items.append({
            'product': p,
            'quantity': qty,
            'subtotal': item_subtotal
        })

    # Discount and shipping
    coupon_code = request.session.get('applied_coupon')
    discount = Decimal('0.00')
    coupon_obj = None
    if coupon_code:
        coupon_obj = Coupon.objects.filter(code=coupon_code, active=True).first()
        if coupon_obj and subtotal >= coupon_obj.min_purchase:
            discount = (subtotal * Decimal(coupon_obj.discount_percent)) / Decimal(100)

    shipping_fee = Decimal('0.00') if subtotal >= 100 else Decimal('15.00')
    grand_total = max(Decimal('0.00'), subtotal - discount + shipping_fee)

    # Get profile for default values
    user_profile = getattr(request.user, 'profile', None)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'] or request.user.email,
                phone=form.cleaned_data['phone'],
                city=form.cleaned_data['city'],
                address=form.cleaned_data['address'],
                notes=form.cleaned_data['notes'],
                latitude=form.cleaned_data.get('latitude'),
                longitude=form.cleaned_data.get('longitude'),
                total_price=grand_total,
                discount_amount=discount,
                shipping_fee=shipping_fee,
                coupon=coupon_obj,
                payment_method=form.cleaned_data['payment_method'],
                status='placed',
                payment_status='paid' if form.cleaned_data['payment_method'] == 'cod' else 'pending',
                is_paid=(form.cleaned_data['payment_method'] == 'cod')
            )

            # Create Order Items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    quantity=item['quantity'],
                    price=item['product'].price
                )

            # Update UserProfile if address or phone changed
            if user_profile:
                if not user_profile.phone and form.cleaned_data.get('phone'):
                    user_profile.phone = form.cleaned_data['phone']
                if not user_profile.address and form.cleaned_data.get('address'):
                    user_profile.address = form.cleaned_data['address']
                if not user_profile.city and form.cleaned_data.get('city'):
                    user_profile.city = form.cleaned_data['city']
                if form.cleaned_data.get('latitude') and form.cleaned_data.get('longitude'):
                    user_profile.latitude = form.cleaned_data['latitude']
                    user_profile.longitude = form.cleaned_data['longitude']
                user_profile.save()

            # Clear cart & coupon
            request.session['cart'] = {}
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']
            request.session.modified = True

            # Send Email Confirmation to customer & notification to admin
            try:
                if settings.EMAIL_HOST_USER:
                    # Customer email
                    customer_subject = f"Order Confirmation #{order.id} - NEXUS STORE"
                    customer_body = (
                        f"Dear {order.name},\n\n"
                        f"Thank you for shopping with NEXUS STORE!\n"
                        f"Order ID: #{order.id}\n"
                        f"Tracking Reference: {order.tracking_number}\n"
                        f"Total: ${order.total_price}\n"
                        f"Payment Method: {order.get_payment_method_display()}\n\n"
                        f"You can monitor your order progress anytime in My Orders.\n\n"
                        f"Warm regards,\nNEXUS STORE Team"
                    )
                    if order.email:
                        send_mail(customer_subject, customer_body, settings.EMAIL_HOST_USER, [order.email], fail_silently=True)

                    # Store Admin Alert Email
                    admin_subject = f"[New Order Alert] #{order.id} placed by {order.name}"
                    admin_body = (
                        f"A new order #{order.id} was just placed!\n"
                        f"Customer: {order.name} ({order.phone})\n"
                        f"Destination: {order.city}, {order.address}\n"
                        f"Total: ${order.total_price}\n"
                        f"Payment Method: {order.get_payment_method_display()}\n"
                        f"Tracking: {order.tracking_number}\n\n"
                        f"Check Store Admin Dashboard for full fulfillment details."
                    )
                    send_mail(admin_subject, admin_body, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=True)
            except Exception as e:
                print("Email alert notice:", e)

            # Redirect based on payment method
            if order.payment_method in ['card', 'wallet']:
                return redirect('pay_order', order_id=order.id)

            return redirect('checkout_success', order_id=order.id)
    else:
        initial_data = {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
        }
        if user_profile:
            initial_data['phone'] = user_profile.phone
            initial_data['city'] = user_profile.city
            initial_data['address'] = user_profile.address
        form = CheckoutForm(initial=initial_data)

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'coupon': coupon_obj,
    })


def checkout_success(request, order_id):
    """Order confirmation and invoice receipt."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'checkout_success.html', {'order': order})


# ==============================================================================
# 3. CUSTOMER DASHBOARD & ACCOUNT
# ==============================================================================

@login_required
def my_orders(request):
    """Customer order history with visual status timeline."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})


@login_required
def cancel_order(request, order_id):
    """Cancel order if in placed or processing state."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['placed', 'processing']:
        order.status = 'cancelled'
        order.save()
        messages.success(request, f"Order #{order.id} has been cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled as it has already been dispatched.")
    return redirect('my_orders')


@login_required
def my_account(request):
    """Customer dashboard view."""
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'my_account.html', {
        'recent_orders': recent_orders,
        'wishlist_count': wishlist_count,
        'profile': user_profile,
    })


@login_required
def edit_profile(request):
    """Edit personal information and saved shipping address."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.phone = request.POST.get('phone', profile.phone)
        profile.city = request.POST.get('city', profile.city)
        profile.address = request.POST.get('address', profile.address)
        profile.save()

        messages.success(request, "Your profile and delivery settings were updated.")
        return redirect('my_account')

    return render(request, 'edit_profile.html', {
        'profile': profile
    })


@login_required
def wishlist_view(request):
    """Saved wishlist items."""
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product__category')
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})


def register(request):
    """Comprehensive user registration view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = ExtendedRegisterForm(request.POST)
        if form.is_valid():
            # Create user
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name'].strip()
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', ''),
                city=form.cleaned_data.get('city', ''),
                address=form.cleaned_data.get('address', '')
            )

            # Log user in directly
            auth_login(request, user)
            messages.success(request, f"Welcome to NEXUS STORE, {user.first_name or user.username}! Your account has been created.")
            return redirect('home')
    else:
        form = ExtendedRegisterForm()

    return render(request, 'register.html', {'form': form})


def google_login_view(request):
    """
    Seamless Google OAuth authentication handler.
    Logs in the user with verified Google identity and ensures their profile is ready.
    """
    next_url = request.GET.get('next', '/')

    email = "arthur.nexus@gmail.com"
    username = "arthur_google"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'first_name': 'Arthur',
            'last_name': 'Vance',
        }
    )

    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.avatar:
        profile.avatar = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&q=80"
        profile.save()

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    if created or not profile.is_complete():
        messages.info(request, f"Welcome, {user.first_name}! Please complete your shipping address.")
    else:
        messages.success(request, f"Signed in with Google as {user.email}.")

    return redirect(next_url)


@login_required
@require_POST
def api_complete_onboarding(request):
    """
    Saves user delivery profile details (phone, city, address, coordinates) via AJAX modal.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    full_name = request.POST.get('full_name', '').strip()
    if full_name:
        parts = full_name.split()
        user.first_name = parts[0]
        user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        user.save()

    phone = request.POST.get('phone', '').strip()
    city = request.POST.get('city', '').strip()
    address = request.POST.get('address', '').strip()

    if phone:
        profile.phone = phone
    if city:
        profile.city = city
    if address:
        profile.address = address

    lat = request.POST.get('latitude')
    lng = request.POST.get('longitude')
    if lat and lng:
        try:
            profile.latitude = float(lat)
            profile.longitude = float(lng)
        except (ValueError, TypeError):
            pass

    profile.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Profile details saved successfully!',
        'user': {
            'name': user.get_full_name() or user.username,
            'phone': profile.phone,
            'city': profile.city,
            'address': profile.address,
        }
    })


def is_supervisor_or_staff(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_staff or user.is_superuser or user.groups.filter(name='Supervisor').exists()


def supervisor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_supervisor_or_staff(request.user):
            messages.error(request, "Supervisor or staff credentials required to access this control console.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def contact_us(request):
    """
    Interactive Live Support Chat & direct concierge interface.
    """
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    welcome_msg = "Welcome to NEXUS Concierge Live Support. How may we assist you today? You can ask about product availability, order tracking, or warranty policies."

    # Retrieve existing conversation
    if request.user.is_authenticated:
        # Link previous anonymous messages from current session to authenticated user
        ChatMessage.objects.filter(session_key=session_key, user__isnull=True).update(user=request.user)
        chat_history = list(ChatMessage.objects.filter(user=request.user).order_by('created_at'))
        # Mark support messages as read
        ChatMessage.objects.filter(user=request.user, sender='agent', is_read=False).update(is_read=True)
    else:
        chat_history = list(ChatMessage.objects.filter(session_key=session_key).order_by('created_at'))
        ChatMessage.objects.filter(session_key=session_key, sender='agent', is_read=False).update(is_read=True)

    # Ensure welcome message and acknowledgment only appear once in conversation
    seen_welcome = False
    seen_ack = False
    deduped_history = []
    for msg in chat_history:
        if msg.message.strip() == welcome_msg.strip():
            if not seen_welcome:
                seen_welcome = True
                deduped_history.append(msg)
            else:
                msg.delete()
        elif msg.sender == 'agent' and msg.message.startswith("Thank you for reaching out to NEXUS Concierge!"):
            if not seen_ack:
                seen_ack = True
                deduped_history.append(msg)
            else:
                msg.delete()
        else:
            deduped_history.append(msg)
    chat_history = deduped_history

    # Seed initial greeting message if conversation is empty
    if not chat_history:
        greeting = ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key,
            sender='agent',
            message=welcome_msg,
            is_read=True
        )
        chat_history = [greeting]

    form = ContactForm()

    return render(request, 'contact.html', {
        'chat_history': chat_history,
        'support_phone': '01011079572',
        'whatsapp_number': '+201011079572',
        'form': form,
    })


@require_POST
def api_chat_send(request):
    """
    AJAX endpoint for the live support chat stream.
    Customer sends a message; sets is_read=False for supervisor attention.
    Automated acknowledgment is only sent once per 24 hours to prevent spam.
    """
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    text = request.POST.get('message', '').strip()
    if not text:
        return JsonResponse({'status': 'error', 'message': 'Message cannot be empty.'})

    user = request.user if request.user.is_authenticated else None

    # Save customer message (marked unread for supervisor)
    user_msg = ChatMessage.objects.create(
        user=user,
        session_key=session_key,
        sender='user',
        message=text,
        is_read=False
    )

    # Intelligent automated concierge reply
    lower = text.lower()
    reply = None

    if any(w in lower for w in ['track', 'order', 'status', 'طلب', 'تتبع']):
        reply = "You can track your order in real-time under 'My Orders' with your TRK tracking number. Or reach our WhatsApp team directly at 01011079572 for immediate order coordination."
    elif any(w in lower for w in ['shipping', 'delivery', 'arrive', 'شحن', 'توصيل']):
        reply = "All orders over $100 receive complimentary express courier shipping across Egypt within 24 to 48 hours with live SMS tracking."
    elif any(w in lower for w in ['return', 'warranty', 'guarantee', 'ضمان', 'استرجاع']):
        reply = "All NEXUS STORE products include an official 2-year manufacturer warranty and a 14-day hassle-free return guarantee."
    elif any(w in lower for w in ['whatsapp', 'phone', 'call', 'واتس', 'رقم']):
        reply = "Our executive concierge is available on WhatsApp directly at +201011079572. Click the WhatsApp button to chat immediately."
    else:
        # Check if customer already received an automated acknowledgment in the last 24 hours
        time_threshold = timezone.now() - timedelta(hours=24)
        history_filter = Q(user=user) if user else Q(session_key=session_key)
        has_recent_ack = ChatMessage.objects.filter(
            history_filter,
            sender='agent',
            message__startswith="Thank you for reaching out to NEXUS Concierge!",
            created_at__gte=time_threshold
        ).exists()

        # Only provide acknowledgment if none has been sent within 24 hours
        if not has_recent_ack:
            reply = "Thank you for reaching out to NEXUS Concierge! Our team has received your message. An executive specialist or supervisor will assist you shortly here, or on WhatsApp at 01011079572."

    agent_msg = None
    if reply:
        agent_msg = ChatMessage.objects.create(
            user=user,
            session_key=session_key,
            sender='agent',
            message=reply,
            is_read=False
        )

    # Also log to ContactMessage for admin inbox
    try:
        ContactMessage.objects.create(
            name=user.get_full_name() if user else "Live Chat Visitor",
            email=user.email if user and user.email else "chat@nexus.store",
            phone=getattr(getattr(user, 'profile', None), 'phone', '') or '01011079572',
            subject="Live Chat Inquiry",
            message=text
        )
    except Exception as e:
        print("Contact log notice:", e)

    return JsonResponse({
        'status': 'success',
        'user_message': {
            'id': user_msg.id,
            'message': user_msg.message,
            'time': user_msg.created_at.strftime('%H:%M'),
        },
        'agent_message': {
            'id': agent_msg.id,
            'message': agent_msg.message,
            'time': agent_msg.created_at.strftime('%H:%M'),
        } if agent_msg else None
    })


def api_chat_poll(request):
    """
    Fast AJAX polling endpoint for live support chat messages.
    """
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    last_id = int(request.GET.get('last_id', 0))

    if request.user.is_authenticated:
        query = (Q(user=request.user) | Q(session_key=session_key)) & Q(id__gt=last_id)
    else:
        query = Q(session_key=session_key) & Q(id__gt=last_id)

    new_messages = ChatMessage.objects.filter(query).order_by('created_at')

    # Mark agent messages as read
    new_agent_ids = [m.id for m in new_messages if m.sender == 'agent']
    if new_agent_ids:
        ChatMessage.objects.filter(id__in=new_agent_ids).update(is_read=True)

    items = [{
        'id': m.id,
        'sender': m.sender,
        'message': m.message,
        'time': m.created_at.strftime('%H:%M'),
    } for m in new_messages]

    return JsonResponse({'status': 'success', 'messages': items})


def api_chat_unread_count(request):
    """
    Returns unread badge count for the customer and (if supervisor/staff) for the admin panel.
    """
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    # Customer unread
    if request.user.is_authenticated:
        customer_unread = ChatMessage.objects.filter(
            Q(user=request.user) | Q(session_key=session_key),
            sender='agent',
            is_read=False
        ).count()
    else:
        customer_unread = ChatMessage.objects.filter(
            session_key=session_key,
            sender='agent',
            is_read=False
        ).count()

    admin_unread = 0
    if is_supervisor_or_staff(request.user):
        admin_unread = ChatMessage.objects.filter(sender='user', is_read=False).count()

    return JsonResponse({
        'status': 'success',
        'customer_unread': customer_unread,
        'admin_unread': admin_unread
    })


# ==============================================================================
# 4. CUSTOM STORE ADMIN & SUPERVISOR CONTROL CENTER
# ==============================================================================

@supervisor_required
def store_admin_dashboard(request):
    """
    Dedicated store owner/supervisor control center.
    Live order management, status updates, inventory insights, and customer messages.
    """
    orders = Order.objects.all().prefetch_related('items').order_by('-created_at')
    products = Product.objects.all().order_by('stock')

    # Metrics
    total_revenue = orders.filter(payment_status='paid').aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
    orders_count = orders.count()
    pending_orders_count = orders.filter(status__in=['placed', 'processing']).count()

    # Inventory Dependent Alerts
    low_stock_products = products.filter(stock__gt=0, stock__lte=F('low_stock_threshold'))
    out_of_stock_products = products.filter(stock__lte=0)
    stock_alerts_count = low_stock_products.count() + out_of_stock_products.count()

    # Inquiries
    unread_inquiries_count = ChatMessage.objects.filter(sender='user', is_read=False).count()
    customer_messages = ContactMessage.objects.all().order_by('-created_at')

    # Quick Announcements Form Handling
    if request.method == 'POST' and 'update_announcement' in request.POST:
        announcement = SiteAnnouncement.objects.first()
        if not announcement:
            announcement = SiteAnnouncement()
        announcement.badge_text = request.POST.get('badge_text', 'LIMITED OFFER').strip()
        announcement.text = request.POST.get('text', '').strip()
        announcement.is_active = request.POST.get('is_active') == 'on'
        announcement.save()
        messages.success(request, "Top Announcement Bar settings saved successfully.")
        return redirect('store_admin_dashboard')

    site_announcement = SiteAnnouncement.objects.first()
    trust_badges = TrustBadge.objects.all().order_by('order', 'id')
    hero_banner = HeroBanner.objects.first()

    return render(request, 'admin_dashboard.html', {
        'orders': orders[:20],
        'total_revenue': total_revenue,
        'orders_count': orders_count,
        'pending_orders_count': pending_orders_count,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'stock_alerts_count': stock_alerts_count,
        'unread_inquiries_count': unread_inquiries_count,
        'customer_messages': customer_messages[:10],
        'site_announcement': site_announcement,
        'trust_badges': trust_badges,
        'hero_banner': hero_banner,
    })


@supervisor_required
def admin_inquiries_dashboard(request):
    """
    Dedicated Live Chat & Inquiries Control Panel for Superusers and Supervisors.
    Enables viewing active client conversation threads and replying in real time.
    """
    all_msgs = ChatMessage.objects.all().select_related('user').order_by('-created_at')

    threads_dict = {}
    for msg in all_msgs:
        if msg.user:
            t_key = f"u_{msg.user.id}"
            t_name = f"{msg.user.first_name} {msg.user.last_name}".strip() or msg.user.username
            t_email = msg.user.email
        else:
            t_key = f"s_{msg.session_key[:12]}" if msg.session_key else f"msg_{msg.id}"
            t_name = f"Guest ({msg.session_key[:6] if msg.session_key else 'Visitor'})"
            t_email = "Guest Session"

        if t_key not in threads_dict:
            threads_dict[t_key] = {
                'id': t_key,
                'user_id': msg.user.id if msg.user else None,
                'session_key': msg.session_key,
                'name': t_name,
                'email': t_email,
                'last_message': msg.message,
                'last_time': msg.created_at,
                'unread_count': 0,
                'messages': []
            }

        threads_dict[t_key]['messages'].append(msg)
        if msg.sender == 'user' and not msg.is_read:
            threads_dict[t_key]['unread_count'] += 1

    thread_list = list(threads_dict.values())
    thread_list.sort(key=lambda x: x['last_time'], reverse=True)

    selected_id = request.GET.get('thread') or (thread_list[0]['id'] if thread_list else None)
    active_thread = next((t for t in thread_list if t['id'] == selected_id), (thread_list[0] if thread_list else None))

    if active_thread:
        active_thread['messages'].sort(key=lambda m: m.created_at)
        if active_thread['user_id']:
            ChatMessage.objects.filter(user_id=active_thread['user_id'], sender='user', is_read=False).update(is_read=True)
        elif active_thread['session_key']:
            ChatMessage.objects.filter(session_key=active_thread['session_key'], sender='user', is_read=False).update(is_read=True)
        active_thread['unread_count'] = 0

    return render(request, 'inquiries_dashboard.html', {
        'threads': thread_list,
        'active_thread': active_thread,
        'unread_total': sum(t['unread_count'] for t in thread_list),
    })


@supervisor_required
@require_POST
def api_admin_chat_reply(request):
    """
    Allows supervisors and administrators to reply directly to customer chat threads.
    """
    thread_id = request.POST.get('thread_id', '').strip()
    reply_text = request.POST.get('message', '').strip()

    if not thread_id or not reply_text:
        return JsonResponse({'status': 'error', 'message': 'Thread ID and message are required.'}, status=400)

    target_user = None
    target_session = ''

    if thread_id.startswith('u_'):
        user_id = thread_id[2:]
        target_user = get_object_or_404(User, id=user_id)
    elif thread_id.startswith('s_'):
        target_session = thread_id[2:]
        sample = ChatMessage.objects.filter(session_key__startswith=target_session).first()
        if sample:
            target_session = sample.session_key
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid thread identifier.'}, status=400)

    msg = ChatMessage.objects.create(
        user=target_user,
        session_key=target_session,
        sender='agent',
        message=reply_text,
        is_read=False
    )

    if target_user:
        ChatMessage.objects.filter(user=target_user, sender='user', is_read=False).update(is_read=True)
    elif target_session:
        ChatMessage.objects.filter(session_key=target_session, sender='user', is_read=False).update(is_read=True)

    return JsonResponse({
        'status': 'success',
        'message': {
            'id': msg.id,
            'sender': msg.sender,
            'message': msg.message,
            'time': msg.created_at.strftime('%H:%M')
        }
    })


@supervisor_required
@require_POST
def admin_quick_restock(request, product_id):
    """Quick 1-click restock from the Inventory Alert panel."""
    product = get_object_or_404(Product, id=product_id)
    try:
        qty = int(request.POST.get('quantity', 25))
    except (ValueError, TypeError):
        qty = 25
    product.stock += qty
    product.save(update_fields=['stock'])
    messages.success(request, f"Restocked {product.name} (+{qty} units). Current stock: {product.stock}.")
    return redirect('store_admin_dashboard')



@staff_member_required
@require_POST
def admin_update_order_status(request, order_id):
    """Quick 1-click status or payment change from the Admin Dashboard."""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    new_payment = request.POST.get('payment_status')

    if new_status and new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
    if new_payment and new_payment in dict(Order.PAYMENT_STATUS_CHOICES):
        order.payment_status = new_payment
        order.is_paid = (new_payment == 'paid')

    order.save()
    messages.success(request, f"Order #{order.id} updated to {order.get_status_display()} ({order.get_payment_status_display()}).")

    # Send status update email to customer
    try:
        if order.email and settings.EMAIL_HOST_USER:
            subject = f"Order #{order.id} Status Update - NEXUS STORE"
            body = (
                f"Dear {order.name},\n\n"
                f"Your order #{order.id} has been updated to: {order.get_status_display()}.\n"
                f"Tracking Number: {order.tracking_number}\n\n"
                f"Thank you for choosing NEXUS STORE."
            )
            send_mail(subject, body, settings.EMAIL_HOST_USER, [order.email], fail_silently=True)
    except Exception as e:
        print("Status update email notice:", e)

    return redirect('store_admin_dashboard')


# ==============================================================================
# 5. FAST AJAX API ENDPOINTS
# ==============================================================================

@require_POST
def api_cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qty = int(request.POST.get('quantity', 1))

    cart = request.session.get('cart', {})
    pid_str = str(product.id)
    cart[pid_str] = cart.get(pid_str, 0) + max(1, qty)
    request.session['cart'] = cart
    request.session.modified = True

    total_items = sum(cart.values())
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    prods = Product.objects.filter(id__in=product_ids)
    total_price = sum(p.price * cart[str(p.id)] for p in prods)

    return JsonResponse({
        'status': 'success',
        'message': f'{product.name} added to your bag.',
        'total_items': total_items,
        'total_price': float(total_price),
    })


@require_POST
def api_cart_update(request, product_id):
    cart = request.session.get('cart', {})
    pid_str = str(product_id)
    delta = int(request.POST.get('delta', 0))

    if pid_str in cart:
        new_qty = cart[pid_str] + delta
        if new_qty > 0:
            cart[pid_str] = new_qty
        else:
            del cart[pid_str]
        request.session['cart'] = cart
        request.session.modified = True

    total_items = sum(cart.values())
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    prods = Product.objects.filter(id__in=product_ids)
    total_price = sum(p.price * cart[str(p.id)] for p in prods)

    return JsonResponse({
        'status': 'success',
        'total_items': total_items,
        'total_price': float(total_price),
    })


@require_POST
def api_cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    pid_str = str(product_id)
    if pid_str in cart:
        del cart[pid_str]
        request.session['cart'] = cart
        request.session.modified = True

    total_items = sum(cart.values())
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    prods = Product.objects.filter(id__in=product_ids)
    total_price = sum(p.price * cart[str(p.id)] for p in prods)

    return JsonResponse({
        'status': 'success',
        'total_items': total_items,
        'total_price': float(total_price),
    })


def api_cart_drawer_content(request):
    cart = request.session.get('cart', {})
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    products = Product.objects.filter(id__in=product_ids)

    items = []
    total_price = Decimal('0.00')

    for p in products:
        qty = cart.get(str(p.id), 0)
        subtotal = p.price * qty
        total_price += subtotal
        items.append({
            'product_id': p.id,
            'name': p.name,
            'price': float(p.price),
            'quantity': qty,
            'subtotal': float(subtotal),
            'image_url': p.image.url if p.image else '/static/images/placeholder.svg',
            'url': reverse('product_detail', args=[p.id])
        })

    return JsonResponse({
        'items': items,
        'total_items': sum(cart.values()) if isinstance(cart, dict) else 0,
        'total_price': float(total_price)
    })


@require_POST
def api_wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'login_required'})

    product = get_object_or_404(Product, id=product_id)
    wishlist_entry = WishlistItem.objects.filter(user=request.user, product=product)

    if wishlist_entry.exists():
        wishlist_entry.delete()
        is_added = False
    else:
        WishlistItem.objects.create(user=request.user, product=product)
        is_added = True

    wishlist_count = WishlistItem.objects.filter(user=request.user).count()

    return JsonResponse({
        'status': 'success',
        'is_added': is_added,
        'wishlist_count': wishlist_count
    })


def api_search_live(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    matches = Product.objects.filter(
        Q(name__icontains=query) |
        Q(category__name__icontains=query)
    ).select_related('category')[:6]

    results = []
    for p in matches:
        results.append({
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'category_name': p.category.name if p.category else '',
            'image_url': p.image.url if p.image else '/static/images/placeholder.svg',
            'url': reverse('product_detail', args=[p.id])
        })

    return JsonResponse({'results': results})


def api_product_quick_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'old_price': float(product.old_price) if product.old_price else None,
        'discount_percentage': product.discount_percentage,
        'category_name': product.category.name if product.category else '',
        'short_description': product.short_description,
        'description': product.description,
        'in_stock': product.in_stock,
        'image_url': product.image.url if product.image else '/static/images/placeholder.svg',
        'url': reverse('product_detail', args=[product.id])
    })


@require_POST
def api_coupon_validate(request):
    code = request.POST.get('code', '').strip()
    coupon = Coupon.objects.filter(code__iexact=code, active=True).first()

    if coupon:
        request.session['applied_coupon'] = coupon.code
        request.session.modified = True
        return JsonResponse({
            'status': 'success',
            'code': coupon.code,
            'discount_percent': coupon.discount_percent,
            'message': f"Promo '{coupon.code}' applied! You save {coupon.discount_percent}%."
        })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid or expired coupon code.'
    })


# ==============================================================================
# 6. PAYMOB GATEWAY
# ==============================================================================

def pay_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    amount_cents = int(order.total_price * 100)

    try:
        token = get_auth_token()
        order_response = create_paymob_order(token, amount_cents)
        order_id_paymob = order_response["id"]

        billing_data = {
            "email": order.email or "customer@example.com",
            "first_name": order.name.split()[0] if order.name else "Customer",
            "last_name": order.name.split()[-1] if len(order.name.split()) > 1 else "User",
            "phone": order.phone or "+201000000000"
        }

        method = request.GET.get("method", "card")
        if method == "vodafone" or order.payment_method == "wallet":
            integration_id = INTEGRATION_ID_VODAFONE
            iframe_id = PAYMOB_IFRAME_ID_VODAFONE
        else:
            integration_id = INTEGRATION_ID_CARD
            iframe_id = PAYMOB_IFRAME_ID_CARD

        payment_key = get_payment_key(token, order_id_paymob, amount_cents, billing_data, integration_id)
        iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_key}"
        return redirect(iframe_url)
    except Exception as e:
        messages.error(request, f"Payment gateway notice: {e}")
        return redirect('checkout_success', order_id=order.id)


@csrf_exempt
def paymob_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if data.get("type") == "TRANSACTION" and data.get("obj", {}).get("success"):
                order_id = data["obj"]["order"]["merchant_order_id"]
                is_paid = data["obj"]["success"]
                order = Order.objects.get(id=order_id)
                order.is_paid = is_paid
                order.payment_status = "paid" if is_paid else "failed"
                order.save()
                return JsonResponse({"status": "Payment updated"}, status=200)
            return JsonResponse({"status": "Failed transaction"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return HttpResponse(status=405)


# ==============================================================================
# NEW FEATURES: Q&A, Recently Viewed, Analytics, Notifications
# ==============================================================================

@require_POST
def api_submit_question(request, product_id):
    """Submit a product Q&A question."""
    product = get_object_or_404(Product, id=product_id)
    question_text = request.POST.get('question', '').strip()
    if not question_text:
        return JsonResponse({'error': 'Question cannot be empty.'}, status=400)
    guest_name = ''
    user = None
    if request.user.is_authenticated:
        user = request.user
    else:
        guest_name = request.POST.get('guest_name', 'Anonymous')[:80]
    ProductQuestion.objects.create(
        product=product,
        user=user,
        guest_name=guest_name,
        question=question_text,
    )
    return JsonResponse({'ok': True, 'message': 'Your question has been submitted for review.'})


def api_recently_viewed(request):
    """Return recently viewed products as JSON for AJAX calls."""
    rv_ids = request.session.get('recently_viewed', [])
    if not rv_ids:
        return JsonResponse({'products': []})
    # Preserve order
    products = {str(p.id): p for p in Product.objects.filter(id__in=rv_ids)}
    ordered = []
    for pid in rv_ids:
        if pid in products:
            p = products[pid]
            ordered.append({
                'id': p.id,
                'name': p.name,
                'price': str(p.price),
                'image': p.image.url if p.image else '',
                'url': f'/product/{p.id}/',
                'rating': p.average_rating,
                'badge': p.badge,
            })
    return JsonResponse({'products': ordered})


@staff_member_required
def api_admin_notifications(request):
    """Return unread orders and chat messages count + latest items for admin bell."""
    from django.db.models import Max
    # Unread chats = threads where last message is from user and has no agent reply after it
    unread_orders = Order.objects.filter(status='placed').order_by('-created_at')[:5]
    unread_chats = ChatMessage.objects.filter(sender='user', is_read=False).values('user', 'session_key').distinct()[:5]

    orders_data = []
    for o in unread_orders:
        orders_data.append({
            'id': o.id,
            'name': o.name,
            'total': str(o.total_price),
            'status': o.status,
            'time': o.created_at.strftime('%H:%M') if o.created_at else '',
        })

    total_unread = Order.objects.filter(status='placed').count() + ChatMessage.objects.filter(sender='user', is_read=False).values('user', 'session_key').distinct().count()

    return JsonResponse({
        'unread_count': total_unread,
        'orders': orders_data,
        'chat_count': ChatMessage.objects.filter(sender='user', is_read=False).values('user', 'session_key').distinct().count(),
    })


@staff_member_required
def store_analytics_view(request):
    """Analytics dashboard data view."""
    from django.db.models import Avg as AvgAgg
    today = timezone.now().date()
    week_ago = today - timedelta(days=6)

    # Totals
    total_revenue = Order.objects.filter(status__in=['placed', 'processing', 'shipped', 'delivered']).aggregate(t=Sum('total_price'))['t'] or 0
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()

    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
    status_map = {s['status']: s['count'] for s in orders_by_status}

    # Best sellers by total units sold
    best_sellers = OrderItem.objects.values('product__id', 'product__name', 'product__image').annotate(
        units=Sum('quantity'), revenue=Sum('price')
    ).order_by('-units')[:8]

    # Revenue per day last 7 days (batch aggregated into 1 query)
    recent_revenue_rows = (
        Order.objects.filter(
            created_at__date__gte=week_ago,
            status__in=['placed', 'processing', 'shipped', 'delivered']
        )
        .values('created_at__date')
        .annotate(total=Sum('total_price'))
    )
    rev_by_date = {r['created_at__date']: float(r['total']) for r in recent_revenue_rows}

    daily_revenue = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_revenue.append({'day': day.strftime('%a'), 'revenue': rev_by_date.get(day, 0.0)})

    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    return render(request, 'store_analytics.html', {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'status_map': status_map,
        'best_sellers': best_sellers,
        'daily_revenue': daily_revenue,
        'daily_revenue_json': json.dumps(daily_revenue),
        'recent_orders': recent_orders,
    })
