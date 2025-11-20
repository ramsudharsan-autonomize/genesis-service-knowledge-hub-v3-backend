# Knowledge Hub V3 Backend

A FastAPI-based backend service for managing datasets and documents in Knowledge Hub V3.

## Features

- **Dataset Management**: Create, retrieve, and manage datasets
- **Document Management**: Handle document operations and storage
- **MongoDB Integration**: Uses Beanie ODM with Motor for async database operations
- **REST API**: Clean RESTful endpoints with automatic OpenAPI documentation

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (via Motor + Beanie ODM)
- **Python**: 3.13+
- **Package Manager**: uv

## Getting Started

### Prerequisites

- Python 3.13 or higher
- MongoDB instance
- uv package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd genesis-service-knowledge-hub-v3-backend
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your MongoDB connection string and other settings
```

3. Install dependencies:
```bash
uv sync
```

### Running the Application

Start the development server:
```bash
uv run uvicorn main:app --reload 
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Datasets
- `POST /api/v3/knowledge_hub/datasets` - Create a new dataset
- `GET /api/v3/knowledge_hub/datasets` - List all datasets
- `GET /api/v3/knowledge_hub/datasets/{id}` - Get a specific dataset

### Documents
- `POST /api/v3/knowledge_hub/documents` - Create a new document
- `GET /api/v3/knowledge_hub/documents` - List all documents
- `GET /api/v3/knowledge_hub/documents/{id}` - Get a specific document

## Project Structure

```
.
├── app/
│   ├── core/          # Database configuration and core setup
│   ├── models/        # Beanie document models
│   ├── routes/        # API route handlers
│   ├── schemas/       # Pydantic schemas for request/response
│   ├── services/      # Business logic layer
│   └── utils/         # Utility functions
├── genesis_common_utility/  # Shared utilities
├── main.py            # Application entry point
└── pyproject.toml     # Project dependencies and metadata
```

## Development

### Running Tests
```bash
uv run pytest
```

### Code Style
This project follows standard Python conventions and uses FastAPI best practices.

```bash
For linting and formatting use Ruff Linter.
```