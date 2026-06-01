# Database Architecture Overview

## Current Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Primary DB | SQLite | (bundled with Python 3.12) |
| ORM | Django ORM | Django 5.2.6 |
| App Server | uWSGI | Python |
| Storage Service | PHP/Apache | 7zip archive handler |

## Application Architecture

```mermaid
graph LR
    subgraph "App1 - Django Gateway"
        A[uWSGI :8000] --> B[Django REST API]
        B --> C[(SQLite db.sqlite3)]
        B --> D[JWT Auth]
    end

    subgraph "App2 - PHP Storage"
        E[Apache :80] --> F[storage.php]
        F --> G[file system storage/]
        E --> H[health.php]
    end

    B -.->|HTTP POST| F