import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_project.settings')
django.setup()

from django.core.management import call_command
from store.models import Category, Product, ProductVariant, Order, OrderItem, ProductImage, Coupon

print("--- Step 1: Clearing existing catalog records to avoid unique constraint conflicts ---")
OrderItem.objects.all().delete()
Order.objects.all().delete()
ProductVariant.objects.all().delete()
ProductImage.objects.all().delete()
Product.objects.all().delete()
Category.objects.all().delete()
Coupon.objects.all().delete()

print("--- Step 2: Loading fresh complete database from datadump.json ---")
call_command('loaddata', 'datadump.json')

print("\n=== SUCCESS: All 20+ products, luxury apparel, variants, images, and categories loaded cleanly! ===")
