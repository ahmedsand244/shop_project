# 💎 NEXUS STORE — Premier Luxury E-Commerce Platform

منصة تجارة إلكترونية متكاملة، حديثة وفائقة السرعة مبنية بواسطة **Django** وتتميز بتصميم فاخر (Luxury Glassmorphism Vector UI)، دعم كامل للوضع الليلي والنهاري (Dark/Light Mode)، لوحة تحكم وإشراف مباشرة (Supervisor & Admin Control Center)، نظام دردشة حية فورية (Live Concierge Chat)، وبوابة دفع Paymob.

---

## 🌟 الميزات الأساسية (Key Features)

1. **واجهة متجر فاخرة (Storefront & Catalog):**
   - تصميم Vector نقي بالكامل بدون إيموجيات مع أيقونات SVG دقيقة.
   - فلترة وتصنيف متقدم للمنتجات (بحث حي Live Search، تصنيفات، فرز بالأسعار والشعبية، عروض الفلاش Flash Deals).
   - بطاقات منتجات ذكية مع تقييمات موثقة، شارات خاصة، وميزة النظرة السريعة (Quick View Modal).

2. **تجربة تسوق سريعة (Cart & One-Page Checkout):**
   - درج سلة جانبي تفاعلي (AJAX Sliding Cart Drawer) للإضافة والتعديل الفوري بدون إعادة تحميل الصفحة.
   - صفحة دفع موحدة (One-Page Checkout) تدعم كود الخصم (Promo Coupons) وحساب الشحن التلقائي.
   - تحديد موقع التوصيل الجغرافي للعميل تلقائياً عبر الـ GPS/Geolocation لإرسال الطلب بدقة.
   - إشعارات فورية وتتبع للطلبات عبر الواتساب (WhatsApp Direct Link) ورسائل البريد الإلكتروني.

3. **خدمة عملاء ودردشة حية (Live Support Concierge):**
   - محادثة دعم حية وسريعة مع ردود ذكية تلقائية.
   - لوحة إشراف خاصة للمشرفين والمديرين للرد المباشر على محادثات الزوار (`/store-admin/inquiries/`).
   - عداد إشعارات وتنبيهات فورية في شريط الإدارة.

4. **لوحة تحكم وتحليلات المتجر (Store Admin & Analytics):**
   - لوحة إدارة مخصصة للمتجر (`/store-admin/`) لمتابعة حالة الطلبات وتحديثها بضغطة زر.
   - تنبيهات أوتوماتيكية عند اقتراب نفاذ المخزون (Low Stock Alerts) مع إمكانية إعادة تزويد المخزون سريعاً.
   - شاشة تحليلات مخصصة مع رسوم بيانية لإيرادات آخر 7 أيام وأفضل المنتجات مبيعاً.

5. **أداء طلقة وسرعة استجابة فائقة (High Performance & Optimization):**
   - تحسين قاعدة بيانات SQLite عبر وضع **WAL Mode** و **64MB RAM Cache** مع `256MB mmap`.
   - كاش فوري في الذاكرة (LocMemCache) لحفظ عناصر المتجر المتكررة.
   - ضغط كامل للمخرجات عبر `GZipMiddleware` بنسبة 80%.
   - القضاء على مشكلة الـ N+1 Queries لتقليل استعلامات الصفحة الرئيسية بنسبة 90%.

---

## 🚀 التشغيل المحلي (Local Development Setup)

### 1. استنساخ المشروع وتثبيت البيئة:
```bash
git clone https://github.com/<YOUR_USERNAME>/shop_project.git
cd shop_project

# إنشاء وتفعيل البيئة الافتراضية
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 2. تثبيت الحزم والمتطلبات:
```bash
pip install -r requirements.txt
```

### 3. إعداد ملف البيئة وتطبيق التهجيرات:
```bash
cp .env.example .env

# تطبيق جداول قاعدة البيانات
python manage.py migrate

# تغذية المتجر ببيانات وفئات ومنتجات تجريبية واقعية
python seed_nexus_data.py

# إنشاء حساب المدير / المشرف
python manage.py createsuperuser
```

### 4. تشغيل السيرفر:
```bash
python manage.py runserver
```
افتح المتصفح على: `http://127.0.0.1:8000/`

---

## 🌐 دليل الرفع الكامل على PythonAnywhere (Step-by-Step Deployment)

اتبع هذه الخطوات البسيطة لرفع وتشغيل الموقع على حساب **PythonAnywhere** المجاني أو المدفوع:

### الخطوة 1: الدخول وإنشاء الـ Bash Console
1. قم بتسجيل الدخول إلى حسابك على [PythonAnywhere](https://www.pythonanywhere.com).
2. من لوحة التحكم (Dashboard)، اذهب إلى قسم **Consoles** وافتح **Bash Console**.

### الخطوة 2: استنساخ المشروع من GitHub
في نافذة الـ Bash، قم بتنفيذ الأوامر التالية:
```bash
# استنساخ المستودع
git clone https://github.com/<YOUR_USERNAME>/shop_project.git

# الدخول للمشروع
cd shop_project
```

### الخطوة 3: إنشاء البيئة الافتراضية وتثبيت المتطلبات
```bash
# إنشاء بيئة افتراضية باسم nexus-env
mkvirtualenv --python=/usr/bin/python3.10 nexus-env

# تثبيت الحزم المطلوبة للمشروع
pip install -r requirements.txt
```

### الخطوة 4: تهيئة ملف الإعدادات وقاعدة البيانات
```bash
# نسخ ملف الإعدادات
cp .env.example .env

# تنفيذ تهجيرات قاعدة البيانات
python manage.py migrate

# تجميع الملفات الثابتة (CSS, JS, Fonts)
python manage.py collectstatic --noinput

# زراعة البيانات المبدئية للمتجر (منتجات وفئات وعروض)
python seed_nexus_data.py

# إنشاء حساب الآدمن للوحة التحكم
python manage.py createsuperuser
```

### الخطوة 5: إعداد الـ Web App من لوحة PythonAnywhere
1. افتح تبويب **Web** في القائمة العلوية واضغط على **Add a new web app**.
2. اختر خيار **Manual configuration** ثم اختر **Python 3.10**.
3. بعد إنشاء التطبيق، قم بضبط الإعدادات التالية في صفحة الـ Web:

#### أ. مسارات المجلدات (Code & Virtualenv paths):
- **Source code:**
  `/home/<YOUR_PYTHONANYWHERE_USERNAME>/shop_project`
- **Working directory:**
  `/home/<YOUR_PYTHONANYWHERE_USERNAME>/shop_project`
- **Virtualenv:**
  `/home/<YOUR_PYTHONANYWHERE_USERNAME>/.virtualenvs/nexus-env`

#### ب. إعداد الملفات الثابتة والمرفوعات (Static Files Mapping):
في قسم **Static files** في نفس الصفحة، أضف السطرين التاليين:

| URL | Directory Path |
|---|---|
| `/static/` | `/home/<YOUR_PYTHONANYWHERE_USERNAME>/shop_project/staticfiles` |
| `/media/` | `/home/<YOUR_PYTHONANYWHERE_USERNAME>/shop_project/media` |

*(ملاحظة: استبدل `<YOUR_PYTHONANYWHERE_USERNAME>` باسم المستخدم الخاص بك في بايثون أني وير)*.

#### ج. ضبط ملف WSGI Configuration:
اضغط على رابط ملف **WSGI configuration file** (بصيغة `/var/www/<username>_pythonanywhere_com_wsgi.py`)، وامسح محتواه بالكامل، ثم الصق الكود التالي:

```python
import os
import sys

# مسار مجلد المشروع
path = '/home/<YOUR_PYTHONANYWHERE_USERNAME>/shop_project'
if path not in sys.path:
    sys.path.append(path)

# تعيين ملف الإعدادات
os.environ['DJANGO_SETTINGS_MODULE'] = 'shop_project.settings'

# تشغيل تطبيق WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
*(احفظ الملف بالضغط على زر **Save** في أعلى اليمين)*.

### الخطوة 6: إعادة تشغيل الموقع (Reload)
ارجع إلى تبويب **Web** واضغط على الزر الأخضر الكبير:
**Reload <your-username>.pythonanywhere.com**

🎉 **مبروك! موقعك الآن يعمل أونلاين على الإنترنت بسرعة وأعلى أداء!**

---

## 🛠️ هيكلية المشروع (Project Architecture)

```
shop_project/
├── manage.py                     # أداة إدارة دجانجو
├── requirements.txt              # متطلبات وحزم المشروع
├── .env.example                  # نموذج المتغيرات البيئية
├── .gitignore                    # الملفات المستثناة من جيت
├── seed_nexus_data.py            # سكربت تغذية المتجر بالبيانات
├── shop_project/
│   ├── settings.py               # إعدادات دجانجو والكاش والوسائط
│   ├── urls.py                   # مسارات المشروع الرئيسية
│   └── wsgi.py                   # مشغل WSGI
└── store/
    ├── models.py                 # جداول المنتجات والطلبات والمحادثات
    ├── views.py                  # دوال العرض والـ APIs السريعة
    ├── urls.py                   # روابط المتجر ولوحة الإدارة
    ├── context_processors.py     # المتغيرات العامة المحسنة والكاش
    ├── static/                   # ملفات CSS والتصميم والأيقونات
    └── templates/                # قوالب HTML الحديثة واللوحات
```

---

## 📄 License
This project is licensed under the MIT License - feel free to customize and deploy it for your commercial needs.
