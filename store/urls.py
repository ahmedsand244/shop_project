from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Catalog & Storefront
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart & Checkout
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase-quantity/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease-quantity/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/<int:order_id>/', views.checkout_success, name='checkout_success'),

    # Customer Dashboard & Orders
    path('my-orders/', views.my_orders, name='my_orders'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('my-account/', views.my_account, name='my_account'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    # Live Support Chat & Supervisor Inquiries
    path('contact/', views.contact_us, name='contact_us'),
    path('chat/', views.contact_us, name='live_chat'),
    path('store-admin/', views.store_admin_dashboard, name='store_admin_dashboard'),
    path('store-admin/inquiries/', views.admin_inquiries_dashboard, name='admin_inquiries_dashboard'),
    path('store-admin/order/<int:order_id>/update-status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('store-admin/product/<int:product_id>/quick-restock/', views.admin_quick_restock, name='admin_quick_restock'),

    # Authentication & Password Reset
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('auth/google/', views.google_login_view, name='google_login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # AJAX Endpoints & Live Chat APIs
    path('api/user/complete-onboarding/', views.api_complete_onboarding, name='api_complete_onboarding'),
    path('api/chat/send/', views.api_chat_send, name='api_chat_send'),
    path('api/chat/poll/', views.api_chat_poll, name='api_chat_poll'),
    path('api/chat/unread-count/', views.api_chat_unread_count, name='api_chat_unread_count'),
    path('api/admin/chat/reply/', views.api_admin_chat_reply, name='api_admin_chat_reply'),

    # Fast AJAX API Endpoints
    path('api/cart/add/<int:product_id>/', views.api_cart_add, name='api_cart_add'),
    path('api/cart/update/<int:product_id>/', views.api_cart_update, name='api_cart_update'),
    path('api/cart/remove/<int:product_id>/', views.api_cart_remove, name='api_cart_remove'),
    path('api/cart/drawer-content/', views.api_cart_drawer_content, name='api_cart_drawer_content'),
    path('api/wishlist/toggle/<int:product_id>/', views.api_wishlist_toggle, name='api_wishlist_toggle'),
    path('api/search/live/', views.api_search_live, name='api_search_live'),
    path('api/product/<int:product_id>/quick-view/', views.api_product_quick_view, name='api_product_quick_view'),
    path('api/coupon/validate/', views.api_coupon_validate, name='api_coupon_validate'),

    # Payments & Webhook
    path('pay-order/<int:order_id>/', views.pay_order, name='pay_order'),
    path('paymob/webhook/', views.paymob_webhook, name='paymob_webhook'),

    # New Features: Q&A, Recently Viewed, Analytics, Notifications
    path('api/product/<int:product_id>/question/', views.api_submit_question, name='api_submit_question'),
    path('api/recently-viewed/', views.api_recently_viewed, name='api_recently_viewed'),
    path('api/admin/notifications/', views.api_admin_notifications, name='api_admin_notifications'),
    path('store-admin/analytics/', views.store_analytics_view, name='store_analytics'),
]
