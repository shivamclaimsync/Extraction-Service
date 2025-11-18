# Extraction Service Core

A modular extraction service that uses SQLAlchemy with unified Pydantic models for extracting structured data from clinical notes and storing it in PostgreSQL.

## Architecture

The service follows a layered architecture:

```
extraction_service/
├── core/               # Base classes, registry, exceptions
├── database/           # SQLAlchemy setup, session management, custom types
├── models/             # SQLAlchemy models with PydanticJSONB
├── extractors/         # Extractor implementations (wrap existing LLM tools)
├── repositories/       # Database CRUD operations
├── services/           # Business logic (orchestration)
├── scripts/            # Manual execution and testing scripts
└── config.py           # Configuration settings
```

