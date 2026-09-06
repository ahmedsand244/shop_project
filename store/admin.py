from django.contrib import admin
from django.utils.html import format_html
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Product, ProductImage, ProductVariant,
    Category, Order, OrderItem,
    Coupon, Review, WishlistItem,
    UserProfile, ContactMessage, ChatMessage,
    SiteAnnouncement, TrustBadge, HeroBanner, ProductQuestion
)

# Custom Admin Branding
admin.site.site_header = "NEXUS STORE — Executive Operations"
admin.site.site_title = "NEXUS Admin"
admin.site.index_title = "Commercial Operations & Catalog Management"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'old_price', 'stock', 'badge', 'is_featured', 'views_count', 'created_at')
    list_editable = ('price', 'stock', 'badge', 'is_featured')
    list_filter = ('category', 'badge', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_featured', 'order')
    list_editable = ('is_featured', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'quantity', 'price', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tracking_number', 'name', 'phone', 'total_price',
        'payment_method', 'payment_status', 'status', 'whatsapp_alert', 'created_at'
    )
    list_editable = ('status', 'payment_status')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('name', 'phone', 'email', 'tracking_number')
    readonly_fields = ('tracking_number', 'total_price', 'latitude', 'longitude', 'whatsapp_action_button', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

    def whatsapp_alert(self, obj):
        if obj.phone:
            url = obj.whatsapp_tracking_url()
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer" style="background:#25D366;color:#fff;font-weight:700;font-size:0.75rem;padding:4px 9px;border-radius:4px;text-decoration:none;display:inline-block;">'
                'WhatsApp Alert'
                '</a>',
                url
            )
        return "-"
    whatsapp_alert.short_description = "WhatsApp"

    def whatsapp_action_button(self, obj):
        if obj.phone:
            url = obj.whatsapp_tracking_url()
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;font-weight:700;font-size:0.9rem;padding:10px 18px;border-radius:6px;text-decoration:none;display:inline-block;box-shadow:0 3px 10px rgba(37,211,102,0.3);">'
                'Open WhatsApp to Send Tracking Link'
                '</a>'
                '<p style="color:#666;font-size:0.8rem;margin-top:6px;">Target number: {}</p>',
                url, obj.phone
            )
        return "No phone number available"
    whatsapp_action_button.short_description = "Direct WhatsApp Trigger"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Automated email alert upon status change
        if change and 'status' in form.changed_data and obj.email and getattr(settings, 'EMAIL_HOST_USER', None):
            try:
                subject = f"Order #{obj.id} Status Update - NEXUS STORE"
                body = (
                    f"Dear {obj.name},\n\n"
                    f"Your order #{obj.id} has been updated to: {obj.get_status_display()}.\n"
                    f"Tracking Number: {obj.tracking_number}\n\n"
                    f"You can monitor your order progress anytime at http://127.0.0.1:8000/my-orders/\n\n"
                    f"Thank you for choosing NEXUS STORE."
                )
                send_mail(subject, body, settings.EMAIL_HOST_USER, [obj.email], fail_silently=True)
            except Exception as e:
                print("Admin order email status notice:", e)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'address', 'latitude', 'longitude')
    search_fields = ('user__username', 'user__email', 'phone', 'city', 'address')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_read', 'created_at')
    list_editable = ('is_read',)
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'sender', 'short_msg', 'is_read', 'created_at')
    list_filter = ('sender', 'is_read', 'created_at')
    search_fields = ('message', 'session_key', 'user__username')

    def short_msg(self, obj):
        return obj.message[:45]
    short_msg.short_description = "Message Snippet"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'active', 'min_purchase', 'created_at')
    list_editable = ('discount_percent', 'active')
    search_fields = ('code',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')


@admin.register(WishlistItem)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')


@admin.register(SiteAnnouncement)
class SiteAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('badge_text', 'short_text', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    search_fields = ('badge_text', 'text')

    def short_text(self, obj):
        from django.utils.html import mark_safe
        return mark_safe(obj.text[:80])
    short_text.short_description = "Message Preview"


@admin.register(TrustBadge)
class TrustBadgeAdmin(admin.ModelAdmin):
    list_display = ('order', 'title', 'subtitle', 'icon_preview', 'is_active')
    list_display_links = ('title',)
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'subtitle')
    list_filter = ('is_active', 'icon')

    def icon_preview(self, obj):
        return format_html('<span style="font-weight:700; color:#6366f1;">[{}]</span> {}', obj.icon.upper(), obj.get_icon_display())
    icon_preview.short_description = "Icon"


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ('tag', 'short_title', 'product', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    search_fields = ('tag', 'title', 'description')

    def short_title(self, obj):
        from django.utils.html import mark_safe
        return mark_safe(obj.title[:60])
    short_title.short_description = "Headline Preview"


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ('product', 'asker_display', 'short_question', 'has_answer', 'is_visible', 'created_at')
    list_editable = ('is_visible',)
    list_filter = ('is_visible', 'created_at')
    search_fields = ('question', 'product__name', 'user__username', 'guest_name')
    readonly_fields = ('product', 'user', 'guest_name', 'question', 'created_at')
    fields = ('product', 'user', 'guest_name', 'question', 'answer', 'is_visible', 'created_at')

    def asker_display(self, obj):
        return obj.asker_name
    asker_display.short_description = 'Asked By'

    def short_question(self, obj):
        return obj.question[:60] + ('...' if len(obj.question) > 60 else '')
    short_question.short_description = 'Question'

    def has_answer(self, obj):
        from django.utils.html import mark_safe
        if obj.answer:
            return mark_safe('<span style="color:#16a34a;font-weight:700;">✓ Answered</span>')
        return mark_safe('<span style="color:#dc2626;">— Pending</span>')
    has_answer.short_description = 'Answer Status'
