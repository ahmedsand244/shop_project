import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Avg


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True, db_index=True)
    icon = models.CharField(max_length=50, blank=True, default='layers', help_text="Icon identifier e.g. laptop, smartphone, watch, headphones, tag")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or f"cat-{uuid.uuid4().hex[:6]}"
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    BADGE_CHOICES = [
        ('none', 'No Badge'),
        ('sale', 'Sale'),
        ('hot', 'Hot'),
        ('trending', 'Trending'),
        ('new', 'New Arrival'),
        ('limited', 'Limited Edition'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True, null=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=20)
    low_stock_threshold = models.PositiveIntegerField(default=5, help_text="Triggers an automated inventory alert when stock falls to or below this quantity")
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default='none')
    is_featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or f"prod-{uuid.uuid4().hex[:6]}"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        if not self.short_description and self.description:
            clean_desc = self.description.strip()
            self.short_description = clean_desc[:180] + ('...' if len(clean_desc) > 180 else '')

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price and self.old_price > 0:
            saving = ((self.old_price - self.price) / self.old_price) * 100
            return int(round(saving))
        return 0

    @property
    def has_discount(self):
        return self.discount_percentage > 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_out_of_stock(self):
        return self.stock <= 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    @property
    def stock_alert_level(self):
        if self.stock <= 0:
            return 'out_of_stock'
        elif self.stock <= self.low_stock_threshold:
            return 'low_stock'
        return 'healthy'


    @property
    def average_rating(self):
        if hasattr(self, 'annotated_rating') and self.annotated_rating is not None:
            return round(float(self.annotated_rating), 1)
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg is not None else 5.0

    @property
    def reviews_count(self):
        if hasattr(self, 'annotated_reviews_count') and self.annotated_reviews_count is not None:
            return self.annotated_reviews_count
        return self.reviews.count()

    @property
    def full_stars_count(self):
        return int(round(self.average_rating))


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, default='Color')  # 'Color', 'Size'
    value = models.CharField(max_length=100)                  # 'Midnight Black', 'Silver', 'XL'
    color_code = models.CharField(max_length=30, blank=True, help_text="Hex color code e.g. #1e293b")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(default=10, help_text="Discount percentage (e.g. 10 for 10%)")
    active = models.BooleanField(default=True)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% off)"


class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Order Placed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash On Delivery'),
        ('card', 'Credit / Debit Card'),
        ('wallet', 'Mobile Wallet / Vodafone Cash'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=30)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=60, blank=True, unique=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"TRK-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    current_base_url = None

    def get_base_url(self):
        import os
        from django.conf import settings
        if hasattr(self, '_base_url') and self._base_url:
            return self._base_url
        if Order.current_base_url:
            return Order.current_base_url
        env_domain = os.getenv('SITE_DOMAIN', '')
        if env_domain:
            return env_domain.rstrip('/') if env_domain.startswith('http') else f"https://{env_domain}"
        if not settings.DEBUG:
            return "https://shopproject.pythonanywhere.com"
        return "http://127.0.0.1:8000"

    def whatsapp_tracking_url(self, base_url=None):
        """Generates direct WhatsApp tracking notification link with dynamic domain."""
        import urllib.parse
        clean_phone = ''.join(c for c in self.phone if c.isdigit())
        if clean_phone.startswith('01'):
            clean_phone = '2' + clean_phone
        elif clean_phone.startswith('1') and len(clean_phone) == 10:
            clean_phone = '20' + clean_phone

        base = base_url or self.get_base_url()
        tracking_link = f"{base}/my-orders/"

        msg = (
            f"Dear {self.name}, your NEXUS STORE order #{self.id} status is: {self.get_status_display()}.\n"
            f"Tracking Number: {self.tracking_number}\n"
            f"Total: ${self.total_price}\n"
            f"View order updates: {tracking_link}"
        )
        return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

    def __str__(self):
        return f"Order #{self.id} - {self.name} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.product_name and self.product:
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.price * self.quantity

    @property
    def display_name(self):
        if self.product_name:
            return self.product_name
        if self.product:
            return self.product.name
        return "Nexus Tech Item"

    def __str__(self):
        return f"{self.quantity} x {self.display_name}"



class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    title = models.CharField(max_length=150, blank=True, default='')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.product.name} ({self.rating}/5 stars)"


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

    @property
    def subtotal(self):
        return self.quantity * self.product.price


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_entries')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    address = models.TextField(blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    avatar = models.URLField(blank=True, default='')

    def is_complete(self):
        """Check if essential delivery data is filled."""
        return bool(self.phone and self.city and self.address)

    def __str__(self):
        return f"Profile of {self.user.username}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, default='')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    session_key = models.CharField(max_length=60, blank=True, default='')
    sender = models.CharField(max_length=20, default='user', choices=[('user', 'Customer'), ('agent', 'Concierge Support')])
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.message[:30]} ({self.created_at.strftime('%H:%M')})"


class SiteAnnouncement(models.Model):
    badge_text = models.CharField(max_length=60, default="LIMITED OFFER", verbose_name="Badge Pill Text")
    text = models.TextField(
        default="Use code <strong>SAVE10</strong> for 10% off • Complimentary express shipping on orders over $100",
        verbose_name="Announcement Content",
        help_text="The promotional text. Basic HTML like <strong> is allowed."
    )
    is_active = models.BooleanField(default=True, verbose_name="Active (Show on site)")
    background_gradient = models.CharField(
        max_length=255,
        default="linear-gradient(90deg, #3730a3 0%, #4f46e5 50%, #7c3aed 100%)",
        blank=True,
        verbose_name="Background CSS Gradient / Color"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Top Announcement Bar"
        verbose_name_plural = "Top Announcement Bar"

    def __str__(self):
        return f"{self.badge_text}: {self.text[:50]}"


class TrustBadge(models.Model):
    ICON_CHOICES = [
        ('truck', 'Truck / Delivery & Shipping'),
        ('shield', 'Shield / Official Warranty'),
        ('lock', 'Lock / Encrypted Checkout & SSL'),
        ('support', 'Concierge / 24/7 Live Support'),
        ('award', 'Award / Quality Guarantee'),
        ('refresh', 'Refresh / Easy 14-Day Returns'),
        ('star', 'Star / Premium Rating'),
        ('credit-card', 'Credit Card / Flexible Payment'),
    ]

    title = models.CharField(max_length=120, verbose_name="Feature Title")
    subtitle = models.CharField(max_length=255, verbose_name="Description / Subtitle")
    icon = models.CharField(max_length=40, choices=ICON_CHOICES, default='truck', verbose_name="Icon")
    order = models.PositiveIntegerField(default=0, verbose_name="Sort Order")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Trust Badge / Store Perk"
        verbose_name_plural = "Trust Badges / Store Perks"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} ({self.get_icon_display()})"


class HeroBanner(models.Model):
    tag = models.CharField(max_length=100, default="FLAGSHIP COLLECTION 2026", verbose_name="Top Tag Pill")
    title = models.CharField(
        max_length=255,
        default="Unrivaled Precision. <br><span class=\"logo-text-gradient\">Pure Innovation.</span>",
        verbose_name="Main Headline (HTML allowed)"
    )
    description = models.TextField(
        default="Engineered for excellence. Explore our hand-curated catalog of advanced hardware, high-fidelity audio, and luxury lifestyle pieces.",
        verbose_name="Description Text"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hero_banners',
        verbose_name="Featured Hero Product (Optional override)"
    )
    product_badge_text = models.CharField(
        max_length=120,
        default="Verified 4.9 Rating • In Stock",
        verbose_name="Product Badge Subtitle"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Home Hero Banner & Showcase"
        verbose_name_plural = "Home Hero Banner & Showcase"

    def __str__(self):
        return f"Hero Banner: {self.tag}"


class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_questions')
    guest_name = models.CharField(max_length=80, blank=True, default='')
    question = models.TextField()
    answer = models.TextField(blank=True, default='', verbose_name='Admin Answer')
    answered_at = models.DateTimeField(null=True, blank=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product Q&A'
        verbose_name_plural = 'Product Q&A'

    def __str__(self):
        return f"Q: {self.question[:50]} → {self.product.name}"

    @property
    def asker_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name or 'Anonymous'
