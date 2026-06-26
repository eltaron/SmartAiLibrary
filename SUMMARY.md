# Smart AI Library — Project Summary for AI Tools

## Overview

Full-stack AI-powered digital library system. Backend: Laravel 12 + FilamentPHP 3. AI layer: 6 Python microservices (FastAPI) running on Docker. Database: MySQL.

---

## Architecture

```
[Mobile App / Frontend]
       |
       v
[Laravel API :8000]  ←── 53 REST endpoints (auth:sanctum)
       |
       ├── [Filament Admin Panel :8000/admin]
       |     8 Resources: Books, Courses, Authors, Categories, Chapters,
       |     Reviews, PersonalShelves, Users, AiMetadata, CourseVideos
       |
       ├── [Laravel DB: MySQL]  ← 23 tables
       |
       └── [AiService Proxy] ──→ [AI Docker Containers]
              POST /api/ai/ingest          → ingestion:8000
              POST /api/ai/recommendations → rec-service:8001
              POST /api/ai/search/semantic → search-service:8002
              POST /api/ai/summarise       → summarise-service:8003
              POST /api/ai/qa/sync         → rag-service:8004
```

---

## Key Directories

| Path | Purpose |
|------|---------|
| `app/Http/Controllers/Api/` | 15 API controllers |
| `app/Http/Resources/Api/` | 5 API resource formatters |
| `app/Models/` | 12 Eloquent models |
| `app/Filament/Resources/` | 8 Filament admin resources |
| `app/Services/AiService.php` | Unified HTTP client for AI microservices |
| `config/ai.php` | AI service URLs & timeouts |
| `database/migrations/` | 23 migration files |
| `database/seeders/` | CourseSeeder, DatabaseSeeder |
| `public/AIGP_FINAL/` | Python AI microservices (6 services) |
| `routes/api.php` | All 53 API routes |

---

## Database — 23 Tables

### Core Entities
| Table | Key Fields | Rows |
|-------|-----------|------|
| `users` | id, name, username, email, role, birth_date, gender | 51 |
| `books` | id, title, slug, author_id, category_id, isbn, cover_image, is_featured, is_free, is_editors_pick | 100 |
| `courses` | id, title, slug, category_id, cover_image, language, duration, average_rating, is_featured, is_free | 6 |
| `authors` | id, name, bio, image, is_narrator | 20 |
| `categories` | id, name, slug, icon, is_active | 10 |

### Relations
| Table | Description |
|-------|-------------|
| `chapters` | Book chapters (audio files + text) |
| `course_videos` | Course videos (video files + text, ordered) |
| `reviews` | User reviews on books (unique: user_id+book_id) |
| `personal_shelves` | User reading shelves (unique: user_id+book_id) |
| `search_histories` | User search history |
| `author_user` | User-followed authors (many-to-many) |
| `category_user` | User interest categories (many-to-many) |

### AI Tables
| Table | Description |
|-------|-------------|
| `ai_metadata` | AI analysis: summary, keywords, entities, sentiment, vector_embeddings |
| `ai_analyses` | Additional AI: short/detailed summary, keywords, topics |

### System Tables
`cache`, `cache_locks`, `sessions`, `jobs`, `job_batches`, `password_reset_tokens`, `personal_access_tokens`

---

## API Routes (53 total)

### Auth (9)
```
register, login, logout, forgot-password/send-otp,
forgot-password/verify-otp, forgot-password/reset,
auth/{provider}/redirect, auth/{provider}/callback
```

### Books & Discovery (13)
```
home, discover, discover/trending-20, discover/free-20,
search, search/initial, search/global, search/filter/{type},
search/history/{id}, books/{id}/favorite, books/{id}/block,
books/{id}/listen, books/{id}/share
```

### Favorites (3)
```
favorites/{type}, favorites/book/{id}, favorites/author/{id}
```

### Authors (3)
```
authors, authors/{id}/similar, authors/{id}/profile
```

### Courses (12)
```
courses, courses/featured, courses/free, courses/category/{id},
courses/{id}, courses/{courseId}/videos,
courses/{courseId}/videos/{videoId}
(CRUD for both courses and videos)
```

### Onboarding (3)
```
profile/update, topics, topics/save
```

### AI Services (11)
```
ai/health, ai/ingest, ai/ingest/{isbn}/status,
ai/recommendations, ai/recommendations/cold-start,
ai/search/semantic, ai/search/similar/{isbn},
ai/summarise, ai/summarise/{isbn}/progress,
ai/qa/sync, ai/qa/stream
```

---

## AI Microservices (Python/FastAPI — Docker)

| Service | Port | Endpoints | Description |
|---------|------|-----------|-------------|
| **ingestion** | 8000 | POST `/ingest`, GET `/ingest/{isbn}/status` | Upload PDF/ePub → extract → chunk → Kafka |
| **rec_service** | 8001 | POST `/recommendations`, GET `/recommendations/cold-start` | Hybrid NCF+CBF recommendations |
| **search_service** | 8002 | POST `/search`, POST `/search/similar/{isbn}` | Semantic search with bi-encoder + cross-encoder reranker |
| **summarise_service** | 8003 | POST `/summarise`, GET `/summarise/{isbn}/progress` | FLAN-T5 map-reduce summarisation |
| **rag_service** | 8004 | POST `/qa/sync`, POST `/qa/stream` | RAG Q&A with Groq LLM (sync JSON + SSE streaming) |
| **embedding** | — | (background Kafka consumer) | Chunks → sentence-transformers vectors → Pinecone |

### Infrastructure (Docker)
- PostgreSQL 16, Redis 7, Kafka 7.5 + Zookeeper, Pinecone (cloud)
- Prometheus + Grafana monitoring

---

## Admin Panel (FilamentPHP 3)

**URL:** `/admin` | **Login:** admin@admin.com / password

| Group | Resource | Navigation |
|-------|----------|------------|
| Library | Books, Courses, Authors, Categories, Chapters | Icon per resource |
| Community | Reviews, Personal Shelves | |
| AI Engine | AI Metadata | |
| Administration | Users | |

**Dashboard widgets:** StatsOverview (8 stats cards) + LatestBooksChart (line chart: books vs courses growth)

---

## Installation

```bash
# Laravel
composer install && cp .env.example .env
php artisan key:generate && php artisan storage:link
php artisan migrate --seed
npm install && npm run build && php artisan serve

# AI (Docker) — optional
cd public/AIGP_FINAL
cp .env.example .env   # set PINECONE_API_KEY, GROQ_API_KEY
docker compose -f infra/docker-compose.yml --env-file .env up -d
```
