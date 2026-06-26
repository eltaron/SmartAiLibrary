# 📚 Smart AI Library

نظام مكتبة ذكية مدعوم بالذكاء الاصطناعي لإدارة الكتب والدورات، مع توصيات ذكية وبحث دلالي.

**التقنيات:** Laravel 12 · FilamentPHP 3 · MySQL · REST API · Sanctum · Python AI Microservices

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
composer install
php artisan migrate
php artisan optimize:clear
php artisan serve
```

---

## 🤖 تشغيل خدمات AI (Docker)

خدمات AI عبارة عن 6 مايكروسيرفيسز بـ Python شغالة على Docker.

```bash
cd public/AIGP_FINAL

# نسخ المفاتيح
cp .env.example .env
# عدل ملف .env وحط: PINECONE_API_KEY, GROQ_API_KEY, OPENAI_API_KEY

# تشغيل كل الخدمات
docker compose -f infra/docker-compose.yml --env-file .env up -d
```

| الخدمة | البورت | الوظيفة |
|--------|--------|---------|
| **ingestion** | 8000 | رفع PDF/EPUB → استخراج نص → تقطيع → Kafka |
| **embedding** | — | خلفية: Kafka → متجهات → Pinecone |
| **rec_service** | 8001 | توصيات كتب (NCF + CBF) |
| **search_service** | 8002 | بحث دلالي + إعادة ترتيب |
| **summarise_service** | 8003 | تلخيص بـ FLAN-T5 |
| **rag_service** | 8004 | Q&A على الكتب بـ Groq LLM |

### التحقق من الخدمات

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

> **ملاحظة:** لو مش عايز تشغل Docker دلوقتي، الـ Laravel routes شغالة برضه — هترجع error بدل ما توقف التطبيق.

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

## 📡 API بالكامل

### المصادقة
```
POST   /api/register                    ← تسجيل حساب جديد
POST   /api/login                       ← تسجيل الدخول
POST   /api/logout                      ← تسجيل الخروج
POST   /api/forgot-password/send-otp    ← إرسال OTP
POST   /api/forgot-password/verify-otp  ← التحقق من OTP
POST   /api/forgot-password/reset       ← إعادة تعيين كلمة المرور
GET    /api/auth/{provider}/redirect    ← Facebook/Google login
GET    /api/auth/{provider}/callback    ← callback من Social
```

### الكتب (Books)
```
GET    /api/home                        ← الصفحة الرئيسية (توصيات، مقترحات)
GET    /api/discover                    ← صفحة الاكتشاف
GET    /api/discover/trending-20        ← أشهر 20 كتاب
GET    /api/discover/free-20            ← أفضل 20 كتاب مجاني
GET    /api/search                      ← بحث عام
GET    /api/search/initial              ← بيانات صفحة البحث
GET    /api/search/global               ← بحث شامل
GET    /api/search/filter/{type}        ← بحث متخصص
DELETE /api/search/history/{id?}        ← مسح سجل البحث
POST   /api/books/{id}/favorite         ← إضافة/إزالة مفضلة
POST   /api/books/{id}/block            ← إخفاء كتاب
POST   /api/books/{id}/listen           ← تسجيل استماع
GET    /api/books/{id}/share            ← رابط مشاركة الكتاب
```

### المفضلة (Favorites)
```
GET    /api/favorites/{type}            ← المفضلة (book/author/narator)
POST   /api/favorites/book/{id}         ← Toggle مفضلة كتاب
POST   /api/favorites/author/{id}       ← Toggle متابعة مؤلف
```

### المؤلفون (Authors)
```
GET    /api/authors                     ← قائمة المؤلفين
GET    /api/authors/{id}/similar        ← مؤلفين مشابهين
GET    /api/authors/{id}/profile        ← بروفايل مؤلف
```

### الكورسات (Courses)
```
GET    /api/courses                     ← قائمة الكورسات
GET    /api/courses/featured            ← الكورسات المميزة
GET    /api/courses/free                ← الكورسات المجانية
GET    /api/courses/category/{id}       ← كورسات حسب التصنيف
GET    /api/courses/{id}                ← تفاصيل كورس + فيديوهات
POST   /api/courses                     ← إنشاء كورس
PUT    /api/courses/{id}                ← تحديث كورس
DELETE /api/courses/{id}                ← حذف كورس
GET    /api/courses/{id}/videos         ← فيديوهات الكورس
POST   /api/courses/{id}/videos         ← إضافة فيديو
PUT    /api/courses/{id}/videos/{vidId} ← تحديث فيديو
DELETE /api/courses/{id}/videos/{vidId} ← حذف فيديو
```

### Onboarding
```
POST   /api/profile/update              ← تحديث البروفايل
GET    /api/topics                      ← قائمة الاهتمامات
POST   /api/topics/save                 ← حفظ الاهتمامات
```

### 🤖 AI Services (ربط مع مايكروسيرفيسز AI)

```
GET    /api/ai/health                   ← حالة جميع خدمات AI

POST   /api/ai/ingest                   ← رفع كتاب PDF/EPUB (multipart: file + isbn + title + author)
GET    /api/ai/ingest/{isbn}/status     ← متابعة حالة الرفع

POST   /api/ai/recommendations          ← توصيات مخصصة {user_id, top_k}
GET    /api/ai/recommendations/cold-start ← توصيات Cold-Start {genre, limit}

POST   /api/ai/search/semantic          ← بحث دلالي {query, top_k, filter_genres}
POST   /api/ai/search/similar/{isbn}    ← كتب مشابهة

POST   /api/ai/summarise                ← تلخيص كتاب {isbn, summary_type, include_mindmap}
GET    /api/ai/summarise/{isbn}/progress ← متابعة التلخيص

POST   /api/ai/qa/sync                  ← Q&A (رد كامل مع citations)
POST   /api/ai/qa/stream                ← Q&A (استريمنج SSE tokens)
```

**ملاحظة:** مسارات AI تعمل كـ **Proxy** — Laravel بيستقبل الطلب وبيوجهه لخدمة AI المناسبة. لو الخدمة مش شغالة، بترجع رسالة خطأ بدل ما التطبيق يوقف.

---

## 🗺️ بنية التكامل مع AI

```
[Mobile App]                  [Laravel API]              [AI Microservices]
     │                             │                            │
     ├─ POST /api/ai/search ──────►│                            │
     │                             ├── POST /search ──────────►│ search-service:8002
     │                             │◄───────── results ────────┤
     │◄──── results ───────────────┤                            │
     │                             │                            │
     ├─ POST /api/ai/recommend ───►│                            │
     │                             ├── POST /recommendations ──►│ rec-service:8001
     │                             │◄──── recommendations ──────┤
     │◄── recommendations ────────┤                            │
```

---

## 🛠 أوامر مفيدة

```bash
# مشاهدة أخطاء Laravel
tail -f storage/logs/laravel.log

# مسح الكاش
php artisan optimize:clear

# إعادة تعبئة الداتا (يمسح القديم)
php artisan migrate:fresh --seed

# تشغيل واجهة Tinker
php artisan tinker

# تشغيل التست
php artisan test

# عرض كل الراوتات
php artisan route:list

# مراقبة خدمات AI
docker compose -f public/AIGP_FINAL/infra/docker-compose.yml logs -f
```

---

## 📁 هيكل المشروع

```
SmartAiLibrary/
├── app/
│   ├── Filament/Resources/         ← موارد لوحة التحكم (Books, Courses, Users...)
│   ├── Http/Controllers/Api/       ← API Controllers (Auth, Books, Courses, AI...)
│   ├── Http/Resources/Api/         ← API Resources (JSON response formatters)
│   ├── Models/                      ← موديلات قواعد البيانات
│   └── Services/
│       └── AiService.php           ← كلاس موحد لربط Laravel بخدمات AI
├── config/
│   ├── ai.php                      ← إعدادات URLs و Timeout لخدمات AI
│   └── ...
├── database/
│   ├── migrations/                  ← ترحيلات الجداول
│   └── seeders/                     ← بيانات تجريبية
├── public/
│   └── AIGP_FINAL/                  ← مشروع AI (Python microservices)
├── routes/
│   ├── api.php                     ← جميع مسارات API
│   └── web.php                     ← مسارات الويب
└── storage/app/public/              ← الملفات المرفوعة
```
