# Clinical Data Extraction Service

A high-performance extraction service that uses Pydantic AI and SQLAlchemy to extract structured data from clinical notes and store it in PostgreSQL. The service processes clinical and hospital summaries in parallel, generating a unified hospitalization ID (GUID) for data consistency.

## Features

- **Parallel Extraction**: Runs 11 extractors simultaneously (8 clinical + 3 hospital) for maximum efficiency
- **Unified Hospitalization ID**: Generates a single GUID per document for linking related records
- **Extensible Architecture**: Easy to add new handlers via the handler registry pattern
- **Type-Safe**: Uses Pydantic models for validation and SQLAlchemy for database operations
- **Async/Await**: Fully asynchronous for optimal performance

## Architecture

The service follows a clean, layered architecture with clear separation of concerns:

```
.
├── main.py                    # Entry point
├── config.py                  # Configuration settings
├── pydantic_ai_settings.py   # Pydantic AI configuration
├── core/                      # Core infrastructure
│   ├── exceptions.py          # Custom exception classes
│   └── logging.py             # Logging configuration
├── database/                   # Database layer
│   ├── session.py             # Async database session management
│   ├── base.py                # SQLAlchemy base
│   └── sql_schema/            # Database schema
├── extractors/                # Individual extraction tools
│   ├── clinical_summary_entity/
│   │   ├── presentation/      # Patient presentation extractor
│   │   ├── history/           # Medical history extractor
│   │   ├── findings/          # Clinical findings extractor
│   │   ├── assessment/        # Clinical assessment extractor
│   │   ├── course/            # Hospital course extractor
│   │   ├── follow_up/          # Follow-up plan extractor
│   │   ├── treatments/         # Treatments extractor
│   │   └── labs/              # Lab results extractor
│   └── hospital_admission_summary_card/
│       ├── facility_timing/   # Facility & timing extractor
│       ├── diagnosis/         # Diagnosis extractor
│       └── medication_risk/   # Medication risk extractor
├── handler/                    # Extraction handlers
│   └── clinical_and_hospital_summary_extraction_handler.py
├── services/                   # Service layer
│   └── extraction_service.py  # Main orchestration service
├── repositories/               # Data access layer
│   ├── clinical_summary_repository.py
│   ├── hospital_summary_repository.py
│   └── models/                # SQLAlchemy models
└── scripts/                    # Utility scripts
```

## Data Flow

```
main.py
  └─> ExtractionService (handler registry)
        └─> ClinicalAndHospitalSummaryExtractionHandler
              ├─> Generate hospitalization_id (GUID)
              ├─> Run 11 extractors in parallel
              ├─> Assemble clinical summary (8 extractors)
              ├─> Assemble hospital summary (3 extractors)
              └─> Save both to database in parallel
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- OpenAI API key (or other LLM provider)

### Installation

1. **Clone and setup virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
   # Or use individual variables:
   PG_HOSPITAL_HOST=localhost
   PG_HOSPITAL_PORT=5432
   PG_HOSPITAL_DATABASE=dbname
   PG_HOSPITAL_USER=user
   PG_HOSPITAL_PASSWORD=password

   # LLM Configuration
   OPENAI_API_KEY=your-api-key
   PYDANTIC_AI_MODEL_NAME=openai:gpt-4o-mini

   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=logs/extraction.log
   ```