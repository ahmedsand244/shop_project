import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from store.models import Category, Product, Order, UserProfile, ChatMessage, ContactMessage

client = Client()
print("=== RUNNING ALL PHASE CHECKS ===")

# 1. Google OAuth Route & Session creation
resp = client.get('/auth/google/?next=/checkout/')
assert resp.status_code == 302, f"Google login failed: {resp.status_code}"
assert resp.url == '/checkout/'
user = User.objects.get(email='arthur.nexus@gmail.com')
assert user.is_authenticated
profile = UserProfile.objects.get(user=user)
print("[PASS] 1. Google OAuth Flow (/auth/google/) completed successfully")

# 2. Onboarding Modal Completion API
onboard_data = {
    'full_name': 'Arthur Vance',
    'phone': '+201011223344',
    'city': 'New Cairo',
    'address': '5th Settlement, Street 90, Villa 15',
    'latitude': '30.0123',
    'longitude': '31.4567'
}
resp = client.post('/api/user/complete-onboarding/', onboard_data)
assert resp.status_code == 200
data = resp.json()
assert data['status'] == 'success'
profile.refresh_from_db()
assert profile.phone == '+201011223344'
assert profile.city == 'New Cairo'
assert profile.is_complete() == True
print("[PASS] 2. Profile Onboarding Modal API (/api/user/complete-onboarding/) saved details")

# 3. Checkout with Geolocation coordinates
p = Product.objects.first()
client.post(f'/api/cart/add/{p.id}/', {'quantity': 1})

checkout_data = {
    'name': 'Arthur Vance',
    'email': 'arthur.nexus@gmail.com',
    'phone': '+201011223344',
    'city': 'New Cairo',
    'address': '5th Settlement, Street 90, Villa 15',
    'latitude': 30.0123,
    'longitude': 31.4567,
    'payment_method': 'cod',
    'notes': 'Ring the bell on arrival'
}
resp = client.post('/checkout/', checkout_data)
assert resp.status_code == 302
order = Order.objects.filter(user=user).order_by('-created_at').first()
assert order is not None
assert order.latitude == 30.0123
assert order.longitude == 31.4567
assert 'wa.me' in order.whatsapp_tracking_url()
print(f"[PASS] 3. Checkout Geolocation & WhatsApp Trigger verified (Order #{order.id}, Lat: {order.latitude}, Lng: {order.longitude})")

# 4. WhatsApp-style Live Chat
resp = client.get('/contact/')
assert resp.status_code == 200
assert b'Executive Concierge' in resp.content or b'chat-stream-box' in resp.content

chat_resp = client.post('/api/chat/send/', {'message': 'Hello, can you help me track my order?'})
assert chat_resp.status_code == 200
chat_data = chat_resp.json()
assert chat_data['status'] == 'success'
assert 'agent_message' in chat_data
print(f"[PASS] 4. WhatsApp-style Live Chat working (Agent Reply: '{chat_data['agent_message']['message'][:40]}...')")

# 5. Django Admin Custom Branding & Styling
admin_user = User.objects.filter(is_staff=True).first()
if not admin_user:
    admin_user = User.objects.create_superuser('nexus_admin', 'admin@nexus.store', 'Pass123!')
admin_client = Client()
admin_client.force_login(admin_user)
admin_resp = admin_client.get('/admin/')
assert admin_resp.status_code == 200
assert b'NEXUS' in admin_resp.content
print("[PASS] 5. Django Admin (/admin/) branded and active")

# 6. Database Seeding check
cats_count = Category.objects.count()
prods_count = Product.objects.count()
assert cats_count >= 6, f"Expected >=6 categories, got {cats_count}"
assert prods_count >= 16, f"Expected >=16 products, got {prods_count}"
print(f"[PASS] 6. Database populated with {cats_count} realistic categories & {prods_count} products")

print("=== ALL NEW CRITICAL UPGRADE TESTS PASSED 100%! ===")
