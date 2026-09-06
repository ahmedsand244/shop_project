import os
import django
import urllib.request
import ssl
from pathlib import Path
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_project.settings')
django.setup()

from store.models import Category, Product, ProductImage, Coupon, Review
from django.contrib.auth.models import User

# Disable SSL verification for reliable image downloads
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

media_dir = Path('media/products')
media_dir.mkdir(parents=True, exist_ok=True)

print("--- FLUSHING OLD CATALOG DATA ---")
Product.objects.all().delete()
Category.objects.all().delete()

print("--- SEEDING REALISTIC LUXURY CATEGORIES ---")
categories_data = [
    {
        'name': 'Smartphones & Flagships',
        'slug': 'smartphones-flagships',
        'icon': 'smartphone',
        'order': 1,
        'is_featured': True
    },
    {
        'name': 'Laptops & Workstations',
        'slug': 'laptops-workstations',
        'icon': 'laptop',
        'order': 2,
        'is_featured': True
    },
    {
        'name': 'High-Fidelity Audio',
        'slug': 'high-fidelity-audio',
        'icon': 'headphones',
        'order': 3,
        'is_featured': True
    },
    {
        'name': 'Timepieces & Smartwatches',
        'slug': 'timepieces-smartwatches',
        'icon': 'watch',
        'order': 4,
        'is_featured': True
    },
    {
        'name': 'Smart Living & Workspace',
        'slug': 'smart-living-workspace',
        'icon': 'home',
        'order': 5,
        'is_featured': True
    },
    {
        'name': 'Pro Photography & Optics',
        'slug': 'pro-photography-optics',
        'icon': 'camera',
        'order': 6,
        'is_featured': True
    },
]

category_objs = {}
for cat_data in categories_data:
    cat = Category.objects.create(**cat_data)
    category_objs[cat.slug] = cat
    print(f"Created category: {cat.name}")

print("\n--- SEEDING REALISTIC LUXURY PRODUCTS ---")
products_data = [
    # Smartphones & Flagships
    {
        'category': 'smartphones-flagships',
        'name': 'Apple iPhone 16 Pro Max - 256GB Natural Titanium',
        'slug': 'iphone-16-pro-max-titanium',
        'sku': 'IPH-16PM-NT256',
        'price': Decimal('1299.00'),
        'old_price': Decimal('1499.00'),
        'stock': 28,
        'badge': 'hot',
        'is_featured': True,
        'short_description': 'Featuring aerospace-grade titanium design, Camera Control, 4K 120 fps Dolby Vision, and the revolutionary A18 Pro chip.',
        'description': 'iPhone 16 Pro Max. Crafted with Grade 5 titanium, featuring a new refined micro-blasted finish. Ceramic Shield front is 2x tougher than any smartphone glass. Super Retina XDR display with ProMotion up to 120Hz. A18 Pro chip powers unprecedented graphic performance and battery life for ultimate luxury power users.',
        'image_url': 'https://images.unsplash.com/photo-1591337676887-a217a6970a8a?w=800&q=80',
        'filename': 'iphone_16_pro_max.jpg'
    },
    {
        'category': 'smartphones-flagships',
        'name': 'Samsung Galaxy S25 Ultra 5G - Titanium Obsidian',
        'slug': 'galaxy-s25-ultra-obsidian',
        'sku': 'SM-S25U-OBS512',
        'price': Decimal('1199.00'),
        'old_price': Decimal('1350.00'),
        'stock': 35,
        'badge': 'new',
        'is_featured': True,
        'short_description': '200MP Quad Telephoto Camera, integrated S-Pen, Snapdragon 8 Elite Mobile Platform, and anti-reflective Corning Gorilla Armor glass.',
        'description': 'Meet Galaxy S25 Ultra, the pinnacle of Samsung engineering. Designed with titanium framing and flattened display edges for an immersive viewing experience. Real-time Galaxy AI brings multi-lingual live translations, advanced photo editing, and Circle to Search.',
        'image_url': 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800&q=80',
        'filename': 'galaxy_s25_ultra.jpg'
    },
    {
        'category': 'smartphones-flagships',
        'name': 'Google Pixel 9 Pro XL - Porcelain 256GB',
        'slug': 'pixel-9-pro-xl-porcelain',
        'sku': 'GOOG-P9PXL-POR',
        'price': Decimal('1099.00'),
        'old_price': Decimal('1199.00'),
        'stock': 18,
        'badge': 'trending',
        'is_featured': False,
        'short_description': 'Tensor G4 processor with 16GB RAM, Super Actua display, and Gemini Nano AI deeply integrated across camera and voice.',
        'description': 'The all-new Google Pixel 9 Pro XL features a silky matte glass back and polished metal frame with dual-finish camera bar. Includes 7 years of Pixel Feature Drops and OS updates. Unbeatable computational photography with 30x Super Res Zoom.',
        'image_url': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80',
        'filename': 'pixel_9_pro.jpg'
    },

    # Laptops & Workstations
    {
        'category': 'laptops-workstations',
        'name': 'Apple MacBook Pro 16-inch M4 Max - Space Black',
        'slug': 'macbook-pro-16-m4-max',
        'sku': 'MBP-16-M4M-36GB',
        'price': Decimal('3499.00'),
        'old_price': Decimal('3899.00'),
        'stock': 12,
        'badge': 'limited',
        'is_featured': True,
        'short_description': '16-core CPU, 40-core GPU, 36GB Unified Memory, Liquid Retina XDR with Nano-Texture glass, up to 24 hours battery life.',
        'description': 'Built for extreme workflows, 3D rendering, machine learning models, and 8K ProRes video grading. The M4 Max chip features hardware-accelerated ray tracing and breakthrough unified memory architecture. Space Black anodization dramatically reduces fingerprints.',
        'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80',
        'filename': 'macbook_pro_16.jpg'
    },
    {
        'category': 'laptops-workstations',
        'name': 'Dell XPS 16 OLED InfinityEdge Workstation - Platinum',
        'slug': 'dell-xps-16-oled-platinum',
        'sku': 'DELL-XPS16-4K',
        'price': Decimal('2599.00'),
        'old_price': Decimal('2899.00'),
        'stock': 15,
        'badge': 'hot',
        'is_featured': True,
        'short_description': 'Intel Core Ultra 9, NVIDIA GeForce RTX 4070, 4K+ OLED Touchscreen, seamless glass haptic touchpad.',
        'description': 'Crafted with CNC-machined aluminum and Gorilla Glass 3. The tone-on-tone minimalist interior features a capacitive touch function row and zero-lattice keyboard for a truly futuristic typing and creator experience.',
        'image_url': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80',
        'filename': 'dell_xps_16.jpg'
    },
    {
        'category': 'laptops-workstations',
        'name': 'ASUS ROG Zephyrus G16 OLED Gaming Laptop',
        'slug': 'asus-rog-zephyrus-g16',
        'sku': 'ROG-Z16-RTX4080',
        'price': Decimal('2299.00'),
        'old_price': Decimal('2599.00'),
        'stock': 20,
        'badge': 'sale',
        'is_featured': False,
        'short_description': 'Ultra-thin CNC aluminum chassis, 2.5K 240Hz OLED ROG Nebula display, Slash Lighting programmable lid.',
        'description': 'Impossibly thin yet uncompromisingly powerful. Features NVIDIA Ada Lovelace graphics with DLSS 3.5, liquid metal thermal cooling, and dual vapor chamber for whisper-quiet high frame-rate productivity and gaming.',
        'image_url': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=800&q=80',
        'filename': 'asus_rog_g16.jpg'
    },

    # High-Fidelity Audio
    {
        'category': 'high-fidelity-audio',
        'name': 'Sony WH-1000XM5 Wireless Noise-Canceling Headphones',
        'slug': 'sony-wh-1000xm5-silver',
        'sku': 'SNY-WH1000XM5-SLV',
        'price': Decimal('399.00'),
        'old_price': Decimal('449.00'),
        'stock': 45,
        'badge': 'hot',
        'is_featured': True,
        'short_description': 'Industry-leading noise cancelation with two processors and 8 microphones. Hi-Res Audio Wireless and 30-hour battery life.',
        'description': 'Magnificent sound engineered to perfection. Specially developed 30mm carbon fiber composite driver unit enhances high-frequency sensitivity for natural sound quality. Soft-fit leather ensures cloud-like all-day listening comfort.',
        'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
        'filename': 'sony_wh1000xm5.jpg'
    },
    {
        'category': 'high-fidelity-audio',
        'name': 'Bang & Olufsen Beoplay H95 Studio Edition',
        'slug': 'bang-olufsen-beoplay-h95',
        'sku': 'BNO-H95-CHESTNUT',
        'price': Decimal('899.00'),
        'old_price': Decimal('999.00'),
        'stock': 10,
        'badge': 'limited',
        'is_featured': True,
        'short_description': 'Custom titanium drivers, lambskin ear cushions, tactile aluminum dials, and adaptive active noise cancellation.',
        'description': 'Designed for 95 years of acoustic heritage. Masterfully tuned by B&O acoustic engineers to deliver sound that moves you. Foldable design with an aluminum carrying case lined with matching woven fabric.',
        'image_url': 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&q=80',
        'filename': 'beoplay_h95.jpg'
    },
    {
        'category': 'high-fidelity-audio',
        'name': 'Bose QuietComfort Ultra Earbuds - White Smoke',
        'slug': 'bose-quietcomfort-ultra-earbuds',
        'sku': 'BOSE-QCU-EAR',
        'price': Decimal('299.00'),
        'old_price': Decimal('349.00'),
        'stock': 32,
        'badge': 'new',
        'is_featured': False,
        'short_description': 'Breakthrough Bose Immersive Audio spatial sound, CustomTune sound personalization, and world-class quiet.',
        'description': 'Spatial audio brings what you hear right in front of you. CustomTune technology automatically adapts the noise cancellation and sound performance to your specific ears for personalized perfection.',
        'image_url': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&q=80',
        'filename': 'bose_qc_ultra.jpg'
    },

    # Timepieces & Smartwatches
    {
        'category': 'timepieces-smartwatches',
        'name': 'Apple Watch Ultra 2 - 49mm Titanium Ocean Band',
        'slug': 'apple-watch-ultra-2-titanium',
        'sku': 'AW-U2-49TI',
        'price': Decimal('799.00'),
        'old_price': Decimal('899.00'),
        'stock': 24,
        'badge': 'hot',
        'is_featured': True,
        'short_description': 'Rugged aerospace titanium case, 3000-nit display, dual-frequency GPS, 36-hour battery, water-resistant 100m.',
        'description': 'The most capable and rugged Apple Watch ever. Features the breakthrough S9 SiP with Double Tap gesture control, on-device Siri, and precision modular watch faces built for endurance and adventure.',
        'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
        'filename': 'apple_watch_ultra.jpg'
    },
    {
        'category': 'timepieces-smartwatches',
        'name': 'Garmin Fenix 7X Pro Sapphire Solar Edition',
        'slug': 'garmin-fenix-7x-pro-solar',
        'sku': 'GRMN-FNX7X-SLR',
        'price': Decimal('899.00'),
        'old_price': Decimal('999.00'),
        'stock': 16,
        'badge': 'trending',
        'is_featured': True,
        'short_description': 'Solar charging power glass lens, built-in LED flashlight, multi-band GNSS satIQ, up to 37 days in smartwatch mode.',
        'description': 'Conquer every hour with advanced training metrics, 24/7 health and wellness monitoring, TopoActive multi-continent maps, and titanium bezel tested to U.S. military standards for thermal and shock resistance.',
        'image_url': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800&q=80',
        'filename': 'garmin_fenix_7x.jpg'
    },
    {
        'category': 'timepieces-smartwatches',
        'name': 'TAG Heuer Connected Calibre E4 - 45mm Black Titanium',
        'slug': 'tag-heuer-connected-calibre-e4',
        'sku': 'TAG-CAL-E4-TI',
        'price': Decimal('1950.00'),
        'old_price': Decimal('2250.00'),
        'stock': 8,
        'badge': 'limited',
        'is_featured': False,
        'short_description': 'Swiss luxury smartwatch craftsmanship with sapphire crystal, DLC titanium grade 2, and exclusive sports app.',
        'description': 'The ultimate expression of luxury and digital performance. Features high-definition OLED display, golf edition GPS tracking, and heritage mechanical watch face complications inspired by legendary Carrera chronographs.',
        'image_url': 'https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=800&q=80',
        'filename': 'tag_heuer_e4.jpg'
    },

    # Smart Living & Workspace
    {
        'category': 'smart-living-workspace',
        'name': 'Dyson Solarcycle Morph Desk Light - Matte Black',
        'slug': 'dyson-solarcycle-morph-light',
        'sku': 'DYS-SC-MORPH-BLK',
        'price': Decimal('649.00'),
        'old_price': Decimal('749.00'),
        'stock': 19,
        'badge': 'new',
        'is_featured': True,
        'short_description': 'Intelligently tracks local daylight. 4 lights in 1: Task, Indirect, Feature, and Ambient lamp with Heat Pipe cooling.',
        'description': 'Engineered to reduce eyestrain and transform your workspace. 3-Point Revolute motion allows 360-degree positioning. Light quality lasts 60 years thanks to pioneering heat pipe cooling technology.',
        'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80',
        'filename': 'dyson_desk_light.jpg'
    },
    {
        'category': 'smart-living-workspace',
        'name': 'Keychron Q1 Pro Wireless Custom Mechanical Keyboard',
        'slug': 'keychron-q1-pro-wireless',
        'sku': 'KYC-Q1P-RGB-RED',
        'price': Decimal('219.00'),
        'old_price': Decimal('259.00'),
        'stock': 40,
        'badge': 'hot',
        'is_featured': False,
        'short_description': 'Full CNC machined aluminum body, double-gasket acoustic dampening, hot-swappable switches, QMK/VIA programmable.',
        'description': 'A masterclass in tactile luxury. Connects with up to 3 devices wirelessly via Bluetooth 5.1. Features sound-absorbing foams, KSA double-shot PBT keycaps, and south-facing RGB lighting for unmatched typing satisfaction.',
        'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80',
        'filename': 'keychron_q1_pro.jpg'
    },

    # Pro Photography & Optics
    {
        'category': 'pro-photography-optics',
        'name': 'Sony Alpha A7R V Mirrorless Camera Body',
        'slug': 'sony-alpha-a7r-v-body',
        'sku': 'SNY-ILCE-7RM5',
        'price': Decimal('3899.00'),
        'old_price': Decimal('4299.00'),
        'stock': 7,
        'badge': 'limited',
        'is_featured': True,
        'short_description': '61.0MP Full-Frame Exmor R sensor, Dedicated AI processing unit for autofocus tracking, 8-stop image stabilization.',
        'description': 'Revolutionary AI autofocus identifies humans, animals, insects, cars, and airplanes. 8K 24p and 4K 60p video recording with 15+ stops of dynamic range. Dual CFexpress Type A / SD UHS-II card slots in magnesium-alloy weather-sealed body.',
        'image_url': 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&q=80',
        'filename': 'sony_a7r_v.jpg'
    },
    {
        'category': 'pro-photography-optics',
        'name': 'Canon RF 50mm f/1.2L USM Prime Lens',
        'slug': 'canon-rf-50mm-f12-l-usm',
        'sku': 'CAN-RF50-F12L',
        'price': Decimal('2299.00'),
        'old_price': Decimal('2499.00'),
        'stock': 14,
        'badge': 'trending',
        'is_featured': False,
        'short_description': 'Legendary L-series optics with ultra-fast f/1.2 aperture, Air Sphere Coating, and ring-type ultrasonic motor.',
        'description': 'Setting new benchmarks in optical clarity, sharpness, and creamy background bokeh. Designed with dust and weather-resistant seals for uncompromising professional commercial and portrait production.',
        'image_url': 'https://images.unsplash.com/photo-1617005082133-548c4dd27f35?w=800&q=80',
        'filename': 'canon_rf50.jpg'
    }
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for idx, p_info in enumerate(products_data, 1):
    cat = category_objs[p_info['category']]
    local_path = media_dir / p_info['filename']

    # Download image if not already present
    if not local_path.exists():
        try:
            print(f"[{idx}/{len(products_data)}] Downloading image for: {p_info['name']}")
            req = urllib.request.Request(p_info['image_url'], headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as response:
                with open(local_path, 'wb') as f:
                    f.write(response.read())
        except Exception as e:
            print(f"Warning: could not download image for {p_info['name']}: {e}")

    # Create Product
    product = Product.objects.create(
        category=cat,
        name=p_info['name'],
        slug=p_info['slug'],
        sku=p_info['sku'],
        price=p_info['price'],
        old_price=p_info['old_price'],
        stock=p_info['stock'],
        badge=p_info['badge'],
        is_featured=p_info['is_featured'],
        short_description=p_info['short_description'],
        description=p_info['description'],
        image=f"products/{p_info['filename']}" if local_path.exists() else None
    )
    print(f"Created Product #{product.id}: {product.name} (${product.price})")

print("\n--- SEEDING VERIFIED DISCOUNT COUPONS ---")
Coupon.objects.all().delete()
coupons = [
    Coupon(code='SAVE10', discount_percent=10, min_purchase=Decimal('50.00'), active=True),
    Coupon(code='VIP20', discount_percent=20, min_purchase=Decimal('200.00'), active=True),
    Coupon(code='NEXUS50', discount_percent=50, min_purchase=Decimal('500.00'), active=True),
]
Coupon.objects.bulk_create(coupons)
print("Coupons seeded: SAVE10 (10%), VIP20 (20%), NEXUS50 (50%)")

print("\n=== DATABASE SEEDING COMPLETED SUCCESSFULLY! ===")
