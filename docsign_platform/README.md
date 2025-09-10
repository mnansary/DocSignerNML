# DocSign Platform API Documentation

This document provides a complete guide to setting up and using the DocSign Platform API. The API is built with FastAPI and allows for the creation, management, signing, and verification of digital documents.

## Table of Contents

1.  [Project Setup](#1-project-setup)
    *   [Prerequisites](#prerequisites)
    *   [Installation](#installation)
    *   [Database Setup](#database-setup)
    *   [Running the Application](#running-the-application)
2.  [API Endpoint Reference](#2-api-endpoint-reference)
    *   [Authentication](#authentication)
    *   [Envelopes](#envelopes)
    *   [Signing](#signing)
    *   [Verification](#verification)
3.  [Workflow Example](#3-workflow-example)

---

## 1. Project Setup

### Prerequisites

*   Python 3.10+
*   PostgreSQL Server (running and accessible)
*   Redis Server (running and accessible)
*   An active Python virtual environment (e.g., `venv` or `conda`).

### Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd docsign_platform
    ```

2.  **Configure Environment Variables**
    Create a `.env` file in the project root (`docsign_platform/.env`). Use the following template and replace the placeholder values with your actual database credentials and server IPs.

    ```dotenv
    # Application Configuration
    PROJECT_NAME="DocSign Platform API"
    API_V1_STR="/api/v1"

    # Database Configuration (for PostgreSQL)
    DATABASE_URL="postgresql://user:password@hostname:5432/docsign_db"

    # CORS Configuration (use "*" for development)
    BACKEND_CORS_ORIGINS=["*"]

    # Storage Path (relative to the 'backend' directory)
    STORAGE_BASE_PATH="./backend/storage"

    # External Microservice URLs (placeholders)
    SIGNATURE_API_URL="http://myapi.com/signdet"
    OCR_API_URL="http://myapi.com/enocr"
    LLM_API_URL="http://myapi.com/gemma3"

    # Celery Configuration (for Redis)
    CELERY_BROKER_URL="redis://hostname:6379/0"
    CELERY_RESULT_BACKEND="redis://hostname:6379/0"
    ```

3.  **Install Python Dependencies**
    Navigate to the `backend` directory and install the required packages.
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

### Database Setup

The project uses **Alembic** to manage database schema migrations.

1.  **Create the Database**
    Connect to your PostgreSQL server and create the database specified in your `.env` file.
    ```sql
    CREATE DATABASE docsign_db;
    ```

2.  **Configure Alembic**
    Open `backend/alembic.ini` and ensure the `sqlalchemy.url` line matches the `DATABASE_URL` in your `.env` file. (Note: The `migrations/env.py` script will automatically use the `.env` file, but keeping `alembic.ini` in sync is good practice).

3.  **Apply Migrations**
    From the `backend` directory, run the `upgrade` command. This will create all necessary tables in your database.
    ```bash
    alembic upgrade head
    ```

### Running the Application

The application requires two separate processes to run concurrently: the FastAPI web server and the Celery background worker.

1.  **Start the FastAPI Server**
    In your first terminal, from the `backend` directory:
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. Interactive documentation (Swagger UI) can be found at `http://127.0.0.1:8000/docs`.

2.  **Start the Celery Worker**
    In a second terminal, from the `backend` directory:
    ```bash
    celery -A celery_worker.celery_app worker --loglevel=info
    ```
    This worker will listen for and process background tasks, such as finalizing documents.

---

## 2. API Endpoint Reference

All endpoints are prefixed with `/api/v1`.

### Authentication

Currently, the API is open for development purposes. In a production environment, all endpoints (except for the public signing and verification endpoints) should be protected by an authentication mechanism like OAuth2.

---

### Envelopes

Handles the creation and configuration of signing "envelopes".

#### `POST /envelopes/`

Uploads a new PDF document to create a draft envelope.

*   **Request (`multipart/form-data`):**
    *   `file`: The PDF document to be signed.
*   **Response (`200 OK`):**
    ```json
    {
      "id": "c7a4b1f0-1e2d-4c3b-8a4d-5e6f7a8b9c0d"
    }
    ```

#### `GET /envelopes/{envelope_id}/preview/{page_num}`

Returns a PNG image preview of a specific page of the original document.

*   **Response (`200 OK`):**
    *   `Content-Type`: `image/png`
    *   The raw image data.

#### `GET /envelopes/{envelope_id}/download`

Returns the original, unaltered PDF document.

*   **Response (`200 OK`):**
    *   `Content-Type`: `application/pdf`
    *   The raw PDF file data.

#### `POST /envelopes/{envelope_id}/setup`

Configures the envelope with recipients and input fields after they have been placed on the frontend.

*   **Request Body:**
    ```json
    {
      "recipients": [
        { "email": "signer1@example.com", "signing_order": 1 },
        { "email": "signer2@example.com", "signing_order": 2 }
      ],
      "fields": [
        {
          "page_number": 1,
          "type": "signature",
          "x_coord": 15.5,
          "y_coord": 70.2,
          "width": 25.0,
          "height": 5.0,
          "assignee_email": "signer1@example.com"
        }
      ]
    }
    ```
*   **Response (`200 OK`):**
    ```json
    {
      "message": "Envelope template configured successfully."
    }
    ```

#### `POST /envelopes/{envelope_id}/send`

Initiates the signing process by changing the envelope status to "sent" and sending a notification (via the Celery worker) to the first recipient(s).

*   **Response (`200 OK`):**
    ```json
    {
      "message": "Envelope has been sent for signing."
    }
    ```
---

### Signing

Handles the public-facing workflow for signers.

#### `GET /sign/{token}`

Fetches the necessary document data for a specific signer using their unique, secret token.

*   **Response (`200 OK`):**
    ```json
    {
      "envelope_id": "c7a4b1f0-1e2d-4c3b-8a4d-5e6f7a8b9c0d",
      "recipient_email": "signer1@example.com",
      "fields": [
        {
          "id": 1,
          "page_number": 1,
          "type": "signature",
          "x_coord": 15.5,
          // ... other field properties ...
        }
      ]
    }
    ```

#### `POST /sign/{token}`

Submits the signer's completed fields (signatures, text inputs, etc.).

*   **Request Body:**
    ```json
    {
      "fields": [
        { "id": 1, "value": "data:image/png;base64,iVBORw0KG..." },
        { "id": 2, "value": "2025-09-10" }
      ]
    }
    ```
*   **Response (`200 OK`):**
    ```json
    {
      "message": "Document successfully signed. Thank you."
    }
    ```
---

### Verification

Provides a public endpoint to verify the authenticity of a completed document.

#### `POST /verify/`

Checks if a provided document has been altered since it was finalized.

*   **Request (`multipart/form-data`):**
    *   `envelope_id`: The Envelope ID of the document.
    *   `file`: The final, signed PDF document to be verified.
*   **Response (`200 OK`):**
    *   **If Authentic:**
        ```json
        {
          "is_authentic": true,
          "message": "Document is authentic and has not been altered since completion.",
          "envelope_id": "c7a4b1f0-1e2d-4c3b-8a4d-5e6f7a8b9c0d",
          "completed_at": "2025-09-10T21:30:00.123Z"
        }
        ```
    *   **If Altered:**
        ```json
        {
          "is_authentic": false,
          "message": "Verification Failed: The document has been altered or is not the correct version.",
          // ... other details ...
        }
        ```

---

## 3. Workflow Example

1.  **Upload:** A user `POST`s a PDF to `/envelopes/` to get a new `envelope_id`.
2.  **Prepare:** The frontend uses the `envelope_id` to fetch page previews (`/envelopes/{id}/preview/{page}`). The user places fields and adds recipients. The final layout is `POST`ed to `/envelopes/{id}/setup`.
3.  **Send:** The user triggers a `POST` to `/envelopes/{id}/send`. The backend sends a signing link to the first signer (`.../sign.html?token=...`).
4.  **Sign:** The signer clicks the link. The frontend calls `GET /sign/{token}` to get the required fields. The signer fills them out, and the data is `POST`ed to `/sign/{token}`.
5.  **Finalize:** If this was the last signer, a background task is triggered. The Celery worker generates the final PDF and saves its cryptographic hash to the database.
6.  **Verify:** Anyone can now `POST` the final PDF and its `envelope_id` to `/verify/` to confirm its integrity.

### Key Considerations for Your Celery Workflow

#### 1. Idempotency: Designing Tasks That Can Safely Run More Than Once

**What it is:** An idempotent task is one that can be executed multiple times with the same input but will only produce the result once.

**Why it matters:** In a distributed system, things can fail. A network blip might occur *after* your task has finished but *before* it can report its success back to the broker (Redis). The broker, thinking the task failed, might give it to another worker to run again.

**Our `finalize_envelope_task` is NOT idempotent.** If it runs twice, it will:
*   Try to re-generate the audit certificate.
*   Try to re-stamp the document.
*   Try to re-merge the PDFs, potentially creating a duplicate file.
*   Worse, it could fail if it tries to access a temporary file that the first run already deleted.

**How to fix it (The Idempotency Check):**
The best way is to add a "state check" at the very beginning of the task.

```python
# Inside finalize_envelope_task in finalize_document.py

@celery_app.task
def finalize_envelope_task(envelope_id: str):
    db = SessionLocal()
    try:
        envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
        if not envelope:
            # ... handle not found ...
            return

        # --- IDEMPOTENCY CHECK ---
        # If a final hash already exists, the task has already been completed successfully.
        if envelope.final_hash is not None:
            print(f"Task for envelope {envelope_id} has already been completed. Skipping.")
            return
        # --- END OF CHECK ---

        # ... rest of the finalization logic ...
```
This simple check makes the task safe to retry. The first run will complete and set the `final_hash`. Any subsequent, accidental runs for the same `envelope_id` will see that the hash exists and exit immediately.

#### 2. Error Handling and Retries

**What it is:** Celery can automatically retry a task if it fails.

**Why it matters:** Temporary failures are common. The database might be briefly unavailable, or an external service might time out. Instead of failing permanently, the task should wait a bit and try again.

**How to implement it:**
You can bind the task to itself to get access to the `retry` method and configure an automatic retry policy.

```python
# Inside finalize_document.py

# Add 'bind=True' to the decorator
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def finalize_envelope_task(self, envelope_id: str): # 'self' is now the task instance
    """
    Celery task to finalize a signed document.
    """
    # ... (idempotency check from above) ...
    try:
        # ... your main logic ...
        
    except Exception as exc:
        print(f"An error occurred during finalization for envelope {envelope_id}: {exc}")
        # Celery's autoretry_for will handle this automatically.
        # You could also manually retry with: self.retry(exc=exc)
        raise
    finally:
        db.close()

```
*   `bind=True`: This injects the task instance as the first argument, `self`.
*   `autoretry_for=(Exception,)`: This tells Celery to automatically retry on *any* exception. You can make this more specific (e.g., `(DatabaseError, TimeoutError)`).
*   `retry_kwargs`:
    *   `max_retries: 3`: It will try a total of 4 times (the initial attempt + 3 retries).
    *   `countdown: 5`: It will wait 5 seconds before the first retry, then longer for subsequent ones (exponential backoff).

#### 3. Monitoring: Knowing What Your Workers Are Doing

**What it is:** In production, you can't just watch the terminal. You need a dedicated tool to see the status of your tasks and workers.

**Why it matters:** You need to know if tasks are failing, if your queues are getting too long, and if your workers are busy or idle. This is essential for debugging and scaling.

**The Solution: Flower**
**Flower** is the most popular and recommended monitoring tool for Celery. It's a real-time web-based dashboard that shows you:
*   A list of all worker nodes and their status.
*   The number of tasks currently running, waiting, or completed.
*   Details of each task, including its arguments, runtime, and result or error.
*   The ability to restart workers or revoke tasks directly from the UI.

**How to run it:**
1.  Install it: `pip install flower`
2.  Add it to `requirements.txt`.
3.  Run it from a new terminal (from the `backend` directory):
    ```bash
    celery -A celery_worker.celery_app flower
    ```
4.  Open your browser to `http://localhost:5555`.

#### 4. Scaling: Handling More Load

As your application grows, a single worker process might not be enough to handle all the background jobs.

**How to scale:**
*   **Increase Concurrency:** The `-c` flag tells a worker how many child processes to run. `celery -A ... worker -c 8` would run 8 tasks in parallel on one machine.
*   **Add More Workers:** You can run the same Celery worker command on multiple different servers. As long as they all point to the same Redis broker, they will automatically share the workload from the queue. This is how you achieve horizontal scaling.

By keeping idempotency, error handling, monitoring, and scaling in mind, you can take the Celery setup we've built and confidently run it in a production environment.

## Alembic Workflow for the DocSign Platform

### 1. What is Alembic and Why Do We Need It?

**Alembic** is a database migration tool created by the author of SQLAlchemy. Its purpose is to manage and track changes to your database schema in a structured, repeatable, and version-controlled way.

**Think of it like Git, but for your database structure.**

In our project, we defined our database tables using Python classes called **models** (e.g., `Envelope`, `Recipient`, `Field`). However, these Python classes don't automatically create tables in your PostgreSQL database. We need a way to translate our models into SQL `CREATE TABLE` commands and apply them.

Alembic solves several key problems:
*   **Automation:** It automatically compares our SQLAlchemy models to the current state of the database and generates the necessary SQL to sync them up. This avoids manually writing complex and error-prone SQL scripts.
*   **Version Control:** Alembic creates a "version history" of our database schema. Each change (like adding a table or a column) is saved as a migration script in the `migrations/versions` folder. This allows us to upgrade a new database to the latest version or downgrade an existing one if needed.
*   **Team Collaboration:** When multiple developers are working on a project, Alembic ensures that everyone can reliably apply the same schema changes to their local databases, keeping them all in sync.

---

### 2. Our Alembic Setup and Configuration

We performed a three-step setup process to integrate Alembic into our project.

#### Step 2.1: Initialization (`alembic init migrations`)

This command created the essential Alembic infrastructure:
*   **`alembic.ini`:** The main configuration file. We edited this to tell Alembic our database connection URL (`sqlalchemy.url`).
*   **`migrations/`:** A directory to hold all migration-related files.
    *   **`migrations/script.py.mako`:** A template file for generating new migration scripts.
    *   **`migrations/env.py`:** A critical Python script that Alembic runs to configure itself. This is where we bridge the gap between Alembic and our FastAPI application.

#### Step 2.2: The "Magic" in `migrations/env.py`

This was the most important and complex part of the setup. We heavily modified `env.py` to make it "application-aware":

1.  **Finding Our App:** We added `sys.path.insert(0, ...)` to tell Python where to find our `app` directory.
2.  **Finding Our Settings:** We added `from app.core.config import settings`. This allows Alembic to read our `.env` file and know the correct database URL, just like our main application.
3.  **Finding Our Models:** We added `from app.db.base import Base` and imported all our model classes (`Envelope`, `Field`, etc.). This populates the `Base.metadata` object.
4.  **Telling Alembic What to Compare:** We set `target_metadata = Base.metadata`. This is the crucial line that tells Alembic, "This metadata object contains the schema I want my database to look like."
5.  **Reliable Connection:** We bypassed Alembic's default connection logic and used `create_engine(settings.DATABASE_URL)` to create a database engine, ensuring it connects in the exact same way our FastAPI application does.

This configuration ensures that Alembic has a complete and accurate picture of our desired database schema every time it runs.

---

### 3. The Two-Step Migration Workflow We Used

Once configured, managing database changes becomes a simple, repeatable, two-step process.

#### Step 3.1: Generating a Migration (`alembic revision --autogenerate`)

This is the "comparison" step. The command `alembic revision --autogenerate -m "A descriptive message"` does the following:
1.  Loads our application's models via the configured `env.py`.
2.  Connects to the database specified in our `.env` file.
3.  Inspects the current schema of the database (what tables and columns exist).
4.  Compares the database's schema with our models' schema (`target_metadata`).
5.  **Detects the differences.** In our case, it detected that the `envelopes`, `fields`, `recipients`, and `audit_trails` tables were missing.
6.  **Generates a new Python script** inside `migrations/versions/`. This script contains two functions: `upgrade()` and `downgrade()`. The `upgrade()` function has the `op.create_table(...)` commands needed to create the missing tables.

#### Step 3.2: Applying a Migration (`alembic upgrade head`)

This is the "execution" step. The command `alembic upgrade head` does the following:
1.  Connects to the database.
2.  Checks the `alembic_version` table (a special table Alembic creates) to see which migration version the database is currently at.
3.  Finds all the migration scripts in `migrations/versions/` that haven't been applied yet.
4.  Executes the `upgrade()` function of each of those scripts in chronological order.

In our case, it ran the script generated in the previous step, which executed the `CREATE TABLE` SQL commands on our PostgreSQL database, bringing it perfectly in sync with our models. We repeated this process when we needed to modify the `Enum` definition for the `fields` table, creating a clear history of our schema's evolution.