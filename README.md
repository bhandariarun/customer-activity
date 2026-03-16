# Unified Customer Activity Service (Django + DRF)

A Django REST service that syncs customer + support activity data from external mock systems and exposes a unified API.

## Features

- Integrates:
  - CRM customers: `https://jsonplaceholder.typicode.com/users`
  - Support tickets: `https://jsonplaceholder.typicode.com/posts`
- Normalizes into internal schemas:
  - `Customer`: `id, name, email`
  - `Activity`: `external_id, customer, type, title, content, source, created_at`
- Idempotent sync (**no duplicates**) using `(source, external_id)` uniqueness + `update_or_create`
- Robust handling:
  - HTTP failures/timeouts => `502 Bad Gateway`
  - Invalid payload fields => record skipped + returned warnings
  - Activities referencing unknown customers => stored with `customer = null`

## Tech stack

- Python + Django
- Django REST Framework
- SQLite (default)
- Redis (message broker)
- Celery (task queue)
- `requests` for external HTTP calls

---

## Setup

### 1) Create venv + install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

**Environment Configuration:**

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` to set your configuration values. The default Redis configuration should work if Redis is running on `localhost:6379`.

Key environment variables for Redis/Celery:
- `CELERY_BROKER_URL`: Redis URL for task queuing (default: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND`: Redis URL for storing task results (default: same as broker)

### 2) Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3) Start Redis server

This project uses Redis as the message broker for Celery. Make sure Redis is installed and running.

**Install Redis (Ubuntu/Debian):**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Install Redis (macOS with Homebrew):**
```bash
brew install redis
brew services start redis
```

**Install Redis (Windows):**
Download from [redis.io](https://redis.io/download) and run `redis-server.exe`.

**Verify Redis is running:**
```bash
redis-cli ping
# Should respond with "PONG"
```

### 4) Start Celery worker

The application uses Celery for background task processing (AI classification of activities).

**Start the main Celery worker:**
```bash
celery -A core worker -l info
```

**Start the AI-specific worker (recommended for better queue isolation):**
```bash
celery -A core worker -l info -Q ai -c 1
```

Keep these terminals running in the background while the application is active.

### 5) Start server

```bash
python manage.py runserver
```

Server will run at: `http://127.0.0.1:8000/`

---

## Testing

This project includes comprehensive unit and integration tests using Django's test framework and Django REST Framework's test utilities.

### Run Tests

**Run all tests:**
```bash
python manage.py test
```

**Run tests for specific app:**
```bash
python manage.py test apps.customers
python manage.py test apps.supports
```



## Background Tasks

This application uses Celery for asynchronous processing of AI classification tasks on activities.

### Task Queues

- **Main queue**: General tasks
- **AI queue**: AI classification tasks (recommended to run separately for better isolation)

### Monitoring Tasks

**Check active tasks:**
```bash
celery -A core inspect active
```

**Check registered tasks:**
```bash
celery -A core inspect registered
```

**View Celery worker stats:**
```bash
celery -A core inspect stats
```

### Troubleshooting

- **Redis connection issues**: Ensure Redis is running and accessible at the configured URL
- **Tasks not processing**: Check that Celery workers are running and connected to the correct queues
- **Task failures**: Check Celery logs for error details and retry configurations

---

## API Documentation

This project uses [drf-spectacular](https://drf-spectacular.readthedocs.io/) to generate OpenAPI 3.0 schemas and interactive documentation.

### Interactive Documentation

- **Swagger UI**: `http://127.0.0.1:8000/api/schema/swagger/`
- **ReDoc**: `http://127.0.0.1:8000/api/schema/redoc/`

### Raw Schema

- **OpenAPI JSON**: `http://127.0.0.1:8000/api/schema/`

---

## API Endpoints

### Sync external data

**POST** `/api/sync`

Synchronizes customer and activity data from external sources (CRM and support systems). This operation is idempotent - running it multiple times will not create duplicates.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/sync
```

**Response (200 OK):**
```json
{
  "customers_upserted": 10,
  "activities_upserted": 100,
  "activities_orphaned": 0,
  "customer_errors": 0,
  "activity_errors": 0,
  "warnings": []
}
```

**Error Responses:**
- `502 Bad Gateway`: External service failure
- `500 Internal Server Error`: Unexpected error

---

### List customers

**GET** `/api/customers`

Retrieves a paginated list of all customers.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 10)

**Request:**
```bash
curl "http://127.0.0.1:8000/api/customers?page=1&page_size=20"
```

**Response (200 OK):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

---

### Customer activities

**GET** `/api/customers/{id}/activities`

Retrieves all activities for a specific customer, ordered by creation date (newest first).

**Path Parameters:**
- `id`: Customer ID (integer)

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Results per page

**Request:**
```bash
curl "http://127.0.0.1:8000/api/customers/1/activities?page=1&page_size=10"
```

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "external_id": "123",
      "customer_id": 1,
      "type": "ticket",
      "title": "Support Request",
      "content": "Issue description...",
      "source": "support",
      "ai_summary": null,
      "ai_category": null,
      "ai_priority": null,
      "created_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Invalid customer ID or customer not found

---

### List and filter activities

**GET** `/api/activities`

Retrieves a paginated list of all activities with optional filtering.

**Query Parameters:**
- `type` (optional): Filter by activity type (`ticket`, `note`, etc.)
- `source` (optional): Filter by source (`crm`, `support`)
- `customer_id` (optional): Filter by customer ID
- `page` (optional): Page number
- `page_size` (optional): Results per page

**Request Examples:**
```bash
# All activities
curl "http://127.0.0.1:8000/api/activities"

# Filter by source and type
curl "http://127.0.0.1:8000/api/activities?source=support&type=ticket"

# Filter by customer
curl "http://127.0.0.1:8000/api/activities?customer_id=1"
```

**Response (200 OK):**
```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/activities?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "external_id": "123",
      "customer_id": 1,
      "type": "ticket",
      "title": "Support Request",
      "content": "Issue description...",
      "source": "support",
      "ai_summary": "Customer reported login issue",
      "ai_category": "technical",
      "ai_priority": "high",
      "created_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

## Design Questions

### 1) Scaling the System (millions of activities/day)

Key improvements:

- **Move sync to background jobs**:
  - Use Celery/RQ + Redis, or a managed queue (SQS/PubSub).
  - `POST /sync` would enqueue a job and return quickly.
- **Bulk operations**:
  - Replace per-row `update_or_create` loops with bulk upsert patterns.
  - In PostgreSQL: `INSERT ... ON CONFLICT DO UPDATE` via Django bulk utilities or custom SQL.
- **Incremental sync**:
  - Track cursors/watermarks (last updated timestamp, pagination cursor) to fetch deltas instead of full data.
- **Partitioning & indexing**:
  - Proper indexes on `(source, external_id)` and `customer_id`.
  - Consider time-based partitioning for very large activity tables.
- **Separate read/write concerns**:
  - Write to OLTP DB, replicate into a read-optimized store (read replicas / Elasticsearch / analytics DB).
- **Observability**:
  - Structured logging, metrics (sync latency, error rates), tracing, alerting.

### 2) Adding New Integrations

Use a “provider interface” + registry pattern:

- Create an abstract integration contract (e.g. `Integration.fetch()` returning normalized `Customer`/`Activity` objects).
- Each new external system becomes a small module:
  - client (HTTP/auth)
  - normalizer (maps external schema -> internal dataclasses)
- The sync service iterates over enabled integrations from settings, e.g.:

- `INTEGRATIONS = ["crm_jsonplaceholder", "support_jsonplaceholder", "erpnext"]`

This keeps the core sync logic stable and makes adding new systems mostly additive.

### 3) Data Consistency (updates/deletes after sync)

Options (choose based on requirements):

- **Upserts for updates**:
  - If external systems expose `updated_at`, store it and update only when newer.
  - Keep external version/hash to detect changes.
- **Deletions**:
  - Prefer **soft delete** locally (`is_deleted` flag) to preserve history/audit.
  - Periodic reconciliation job:
    - fetch IDs from external system
    - mark missing records as deleted
- **Event-driven** (best when available):
  - Webhooks from external systems for create/update/delete events.
- **Conflict strategy**:
  - Define source-of-truth per field/system and avoid overwriting curated internal fields.

---

## Notes

- This project uses SQLite for simplicity. For production-like usage, switch to PostgreSQL and implement bulk upserts.
- Admin UI available at `/admin/` after creating a superuser:
  ```bash
  python manage.py createsuperuser
  ```