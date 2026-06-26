# 📚 Smart AI Library

نظام مكتبة ذكية مدعوم بالذكاء الاصطناعي لإدارة الكتب والدورات، مع توصيات ذكية وبحث دلالي.

**التقنيات:** Laravel 12 · FilamentPHP 3 · MySQL · REST API · Sanctum

---

## 🚀 طريقة تشغيل المشروع

### ▶️ لو أول مرة تشغل المشروع

```bash
# 1. نسخ المتغيرات البيئية
cp .env.example .env

# 2. تعديل ملف .env - اضبط بيانات قاعدة البيانات
#    DB_DATABASE=smart_library_db
#    DB_USERNAME=root
#    DB_PASSWORD=

# 3. تثبيت مكتبات PHP
composer install

# 4. توليد مفتاح التشفير
php artisan key:generate

# 5. إنشاء رابط التخزين
php artisan storage:link

# 6. تشغيل الترحيلات مع البيانات التجريبية
php artisan migrate --seed

# 7. تثبيت مكتبات前端
npm install
npm run build

# 8. تشغيل السيرفر
php artisan serve
```

### 🔁 لو كان المشروع شغال قبل كده وعايز تحديثه

```bash
# 1. تحديث المكتبات
composer install

# 2. تشغيل أي ترحيلات جديدة (لو في إضافات)
php artisan migrate

# 3. لو عايز تعبي بيانات تجريبية (اختياري)
php artisan db:seed

# 4. مسح الكاش
php artisan optimize:clear

# 5. تشغيل السيرفر
php artisan serve
```

### 🐳 لو عايز تشغل بالـ Docker (Sail)

```bash
composer install
./vendor/bin/sail up -d
./vendor/bin/sail artisan migrate --seed
./vendor/bin/sail npm install && ./vendor/bin/sail npm run build
```

---

## 👨‍💼 لوحة التحكم (Admin Panel)

| البيان | القيمة |
|--------|--------|
| **الرابط** | `http://127.0.0.1:8000/admin` |
| **البريد** | `admin@admin.com` |
| **كلمة المرور** | `password` |

### أقسام لوحة التحكم

#### 📚 Library (المكتبة)
| القسم | الوصف |
|-------|-------|
| **Books** | إدارة الكتب (إضافة/تعديل/حذف) مع رفع الغلاف والملفات |
| **Courses** | إدارة الكورسات التعليمية وفيديوهاتها |
| **Authors** | المؤلفون والرواة مع إمكانية رفع الصور |
| **Categories** | تصنيفات الكتب والكورسات |
| **Chapters** | فصول الكتب الصوتية والمقروءة |

#### 👥 Community (المجتمع)
| القسم | الوصف |
|-------|-------|
| **Reviews** | تقييمات وتعليقات المستخدمين على الكتب |
| **Personal Shelves** | الرفوف الشخصية للمستخدمين (قراءة/مكتمل/مفضل) |

#### 🤖 AI Engine (الذكاء الاصطناعي)
| القسم | الوصف |
|-------|-------|
| **AI Metadata** | بيانات التحليل الذكي للكتب (ملخصات، كلمات مفتاحية، Vector Embeddings) |

#### ⚙️ Administration (الإدارة)
| القسم | الوصف |
|-------|-------|
| **Users** | إدارة المستخدمين والأدوار (admin, researcher, student) |

---

## 📡 API - التوثيق

### المصادقة
```
POST   /api/register                    ← تسجيل حساب جديد
POST   /api/login                       ← تسجيل الدخول
POST   /api/logout                      ← تسجيل الخروج (يحتاج Token)
POST   /api/forgot-password/send-otp    ← إرسال OTP
POST   /api/forgot-password/verify-otp  ← التحقق من OTP
POST   /api/forgot-password/reset       ← إعادة تعيين كلمة المرور

GET    /api/auth/{provider}/redirect    ← تسجيل via Social (facebook/google)
GET    /api/auth/{provider}/callback    ← callback من Social
```

### الكتب (Books)
```
GET    /api/home                        ← الصفحة الرئيسية (توصيات، مقترحات)
GET    /api/discover                    ← صفحة الاكتشاف (تصنيفات + قوائم)
GET    /api/discover/trending-20        ← أشهر 20 كتاب
GET    /api/discover/free-20            ← أفضل 20 كتاب مجاني
GET    /api/search                      ← بحث عام
GET    /api/search/initial              ← بيانات صفحة البحث
GET    /api/search/global               ← بحث شامل
GET    /api/search/filter/{type}        ← بحث متخصص (books/authors/categories)
DELETE /api/search/history/{id?}        ← مسح سجل البحث

POST   /api/books/{id}/favorite         ← إضافة/إزالة مفضلة
POST   /api/books/{id}/block            ← إخفاء كتاب
POST   /api/books/{id}/listen           ← تسجيل استماع
GET    /api/books/{id}/share            ← رابط مشاركة الكتاب
```

### المفضلة (Favorites)
```
GET    /api/favorites/{type}            ← المفضلة حسب النوع (book/author/narator)
POST   /api/favorites/book/{id}         ← Toggle مفضلة كتاب
POST   /api/favorites/author/{id}       ← Toggle متابعة مؤلف
```

### المؤلفون (Authors)
```
GET    /api/authors                     ← قائمة المؤلفين
GET    /api/authors/{id}/similar        ← مؤلفين مشابهين
GET    /api/authors/{id}/profile        ← بروفايل مؤلف
```

### الكورسات (Courses) — جديد
```
GET    /api/courses                     ← قائمة الكورسات
GET    /api/courses/featured            ← الكورسات المميزة
GET    /api/courses/free                ← الكورسات المجانية
GET    /api/courses/category/{id}       ← كورسات حسب التصنيف
GET    /api/courses/{id}                ← تفاصيل كورس + الفيديوهات
POST   /api/courses                     ← إنشاء كورس جديد
PUT    /api/courses/{id}                ← تحديث كورس
DELETE /api/courses/{id}                ← حذف كورس

GET    /api/courses/{id}/videos         ← فيديوهات الكورس
POST   /api/courses/{id}/videos         ← إضافة فيديو (رفع ملف)
PUT    /api/courses/{id}/videos/{vidId} ← تحديث فيديو
DELETE /api/courses/{id}/videos/{vidId} ← حذف فيديو
```

### Onboarding (الإعداد الأولي)
```
POST   /api/profile/update              ← تحديث البروفايل
GET    /api/topics                      ← قائمة الاهتمامات (تصنيفات)
POST   /api/topics/save                 ← حفظ الاهتمامات المختارة
```

### ملاحظات الـ API
- جميع المسارات ما عدا `register/login` تتطلب **Bearer Token** من Sanctum (`auth:sanctum`)
- الـ Token بيتم إرجاعه مع استجابة `/login`
- رفع الملفات (صور، فيديوهات) يتم عبر `multipart/form-data`
- الاستجابات بصيغة JSON مع `status` و `data`

---

## 🛠 أوامر مفيدة

```bash
# مراقبة الأخطاء
tail -f storage/logs/laravel.log

# مسح الكاش بالكامل
php artisan optimize:clear

# إعادة تعبئة الداتا (يمسح القديم)
php artisan migrate:fresh --seed

# تشغيل واجهة Tinker للاختبار
php artisan tinker

# تشغيل التست
php artisan test
```

---

## 📁 هيكل المشروع

```
SmartAiLibrary/
├── app/
│   ├── Filament/Resources/     ← موارد لوحة التحكم
│   ├── Http/Controllers/Api/   ← API Controllers
│   ├── Http/Resources/Api/     ← API Resources (JSON response)
│   └── Models/                  ← موديلات قواعد البيانات
├── config/                      ← إعدادات المشروع
├── database/
│   ├── migrations/              ← ترحيلات الجداول
│   └── seeders/                 ← بيانات تجريبية
├── routes/
│   ├── api.php                  ← مسارات API
│   └── web.php                  ← مسارات الويب
└── storage/app/public/          ← الملفات المرفوعة
```
