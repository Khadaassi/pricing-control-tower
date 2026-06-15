# Pricing Control Tower AI Service

This service contains the AI chatbot API for Pricing Control Tower.

It is independent from the business backend.

## Responsibilities

The AI service is responsible for:

- receiving chatbot requests;
- orchestrating the controlled AI assistant;
- selecting authorized business tools;
- calling the business backend through approved endpoints;
- returning structured chatbot responses.

## Security principles

The AI service must not:

- access PostgreSQL directly;
- generate or execute SQL;
- modify pricing data;
- approve, reject, or apply price changes;
- bypass RBAC rules.

## Project structure

```text
ai_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py
│   └── core/
│       ├── __init__.py
│       └── config.py
├── .env.example
├── .python-version
├── pyproject.toml
├── README.md
└── uv.lock
````

## Run locally

From the `ai_service` directory:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

## Available endpoints

Root endpoint:

```bash
curl http://localhost:8001/
```

Health endpoint:

```bash
curl http://localhost:8001/health
```

OpenAPI documentation:

```text
http://localhost:8001/docs
```

## Current status

At this stage, the service contains only the FastAPI foundation.

The chatbot endpoint, LLM provider, orchestrator, and business tools will be added in later tickets.

## LLM provider configuration

The AI service uses a configurable LLM provider.

The current default provider is Groq.

The provider is selected through environment variables, so the implementation can later be extended to another provider without changing the chatbot orchestrator.

## Environment variables

Create a local `.env` file in the `ai_service/` directory.

Required variables:

```env
LLM_PROVIDER="groq"
LLM_MODEL="llama-3.1-8b-instant"
GROQ_API_KEY="your-groq-api-key"