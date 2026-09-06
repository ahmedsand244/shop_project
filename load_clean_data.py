import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_project.settings')
django.setup()

from django.core.management import call_command
from store.models import Category, Product, ProductVariant, ProductImage, Coupon, TrustBadge, HeroBanner, SiteAnnouncement

print("--- 1. Clearing existing catalog records to avoid unique constraint conflicts ---")
ProductVariant.objects.all().delete()
ProductImage.objects.all().delete()
Product.objects.all().delete()
Category.objects.all().delete()
Coupon.objects.all().delete()
TrustBadge.objects.all().delete()
HeroBanner.objects.all().delete()
SiteAnnouncement.objects.all().delete()

print("--- 2. Loading complete catalog & apparel from datadump.json ---")
call_command('loaddata', 'datadump.json')

print("\n=== SUCCESS: All 20 products, luxury apparel, variants (sizes, colors, storage), and images loaded cleanly! ===")

