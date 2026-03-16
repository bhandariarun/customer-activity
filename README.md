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
- `requests` for external HTTP calls

---

## Setup

### 1) Create venv + install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2) Run migrations

```bash
python manage.py migrate
```

### 3) Start server

```bash
python manage.py runserver
```

Server will run at: `http://127.0.0.1:8000/`

---

## API Endpoints

### Sync external data

**POST** `/sync`

```bash
curl -X POST http://127.0.0.1:8000/sync
```

Example response:

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

Running `/sync` multiple times does **not** create duplicates.

---

### List customers

**GET** `/customers`

```bash
curl http://127.0.0.1:8000/customers
```

---

### Customer activities

**GET** `/customers/{id}/activities`

```bash
curl http://127.0.0.1:8000/customers/1/activities
```

---

### Filter activities

**GET** `/activities?source=support`  
**GET** `/activities?type=ticket`  
(Optional) `customer_id` filter: `/activities?customer_id=1`

```bash
curl "http://127.0.0.1:8000/activities?source=support&type=ticket"
```

---

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