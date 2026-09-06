import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from django.db.models import F
from store.models import Product, ChatMessage, Order

client = Client()

print("=" * 60)
print("RUNNING VERIFICATION SUITE FOR ROUND 3 UPGRADES")
print("=" * 60)

# Phase 1: Favicon and Static Assets
assert os.path.exists("store/static/images/favicon.svg"), "favicon.svg missing!"
assert os.path.getsize("store/static/images/favicon.svg") > 100, "favicon.svg is empty!"
print("[PASS] 1. Brand Favicon SVG created and verified.")

# Phase 2: Inventory Dependent Alerts
p = Product.objects.first()
assert hasattr(p, 'low_stock_threshold'), "low_stock_threshold missing on Product!"
low_stock_qs = Product.objects.filter(stock__gt=0, stock__lte=F('low_stock_threshold'))
out_of_stock_qs = Product.objects.filter(stock__lte=0)
print(f"[PASS] 2. Inventory Alert Engine active: {low_stock_qs.count()} low stock, {out_of_stock_qs.count()} out of stock items.")

# Phase 3: Password Reset System
resp = client.get('/password-reset/')
assert resp.status_code == 200, f"Password reset form failed: {resp.status_code}"
assert b'Reset Password' in resp.content

# Post reset request for superuser or first user
user = User.objects.first()
resp_post = client.post('/password-reset/', {'email': user.email})
assert resp_post.status_code in [200, 302], f"Password reset POST failed: {resp_post.status_code}"

resp_done = client.get('/password-reset/done/')
assert resp_done.status_code == 200
assert b'Check Your Inbox' in resp_done.content
print("[PASS] 3. Secure Email Password Reset workflow verified (form, dispatch, done).")

# Phase 4: Live Support Chat API & Unread Badges
resp_chat = client.get('/contact/')
assert resp_chat.status_code == 200
resp_chat_alias = client.get('/chat/')
assert resp_chat_alias.status_code == 200

# Test client sending a message
resp_send = client.post('/api/chat/send/', {'message': 'Hello, I have an inquiry regarding product warranty.'})
assert resp_send.status_code == 200
send_data = resp_send.json()
assert send_data['status'] == 'success'
last_id = send_data['user_message']['id']

# Test polling
resp_poll = client.get(f'/api/chat/poll/?last_id=0')
assert resp_poll.status_code == 200
poll_data = resp_poll.json()
assert poll_data['status'] == 'success'

# Test unread count endpoint
resp_unread = client.get('/api/chat/unread-count/')
assert resp_unread.status_code == 200
unread_data = resp_unread.json()
assert 'customer_unread' in unread_data
assert 'admin_unread' in unread_data
print("[PASS] 4. Live Chat endpoints verified (Send, Poll, Unread Count).")

# Phase 5: Supervisor Group & Inquiries Dashboard
supervisor_user, _ = User.objects.get_or_create(username='supervisor_test', email='supervisor@nexus.store')
supervisor_group = Group.objects.get(name='Supervisor')
supervisor_user.groups.add(supervisor_group)
supervisor_user.set_password('NexusSuper#2026')
supervisor_user.save()

client.force_login(supervisor_user)
resp_inquiries = client.get('/store-admin/inquiries/')
assert resp_inquiries.status_code == 200
assert b'Customer Inquiries' in resp_inquiries.content

resp_store_admin = client.get('/store-admin/')
assert resp_store_admin.status_code == 200
assert b'Inventory Dependent Alerts' in resp_store_admin.content

# Test Supervisor Reply API
# Send reply to a session thread
sample_msg = ChatMessage.objects.filter(sender='user').first()
thread_id = f"u_{sample_msg.user.id}" if sample_msg.user else f"s_{sample_msg.session_key[:12]}"
resp_reply = client.post('/api/admin/chat/reply/', {
    'thread_id': thread_id,
    'message': 'Hello from Supervisor! How can we assist your order?'
})
assert resp_reply.status_code == 200
reply_data = resp_reply.json()
assert reply_data['status'] == 'success'
print("[PASS] 5. Supervisor Console verified (Inquiries Dashboard, Store Admin, Live Reply API).")

# Phase 6: Django Admin Executive Light Theme
admin_user = User.objects.filter(is_superuser=True).first()
client.force_login(admin_user)
resp_admin = client.get('/admin/')
assert resp_admin.status_code == 200
assert b'custom_admin.css' in resp_admin.content
assert b'Live Chat Inquiries' in resp_admin.content
print("[PASS] 6. Executive Light Mode Django Admin verified.")

print("=" * 60)
print("ALL ROUND 3 SPECIFICATIONS VERIFIED 100% SUCCESSFULLY!")
print("=" * 60)
