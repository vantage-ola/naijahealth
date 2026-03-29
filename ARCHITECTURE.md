Daily Cron Job
     │
     ▼
Playwright Scraper
     │
     ▼
Pydantic Validation ──► PostgreSQL
                              │
                         Embedding Job
                              │
                              ▼
                            Qdrant
                              │
                    ┌─────────┴──────────┐
                    │                    │
               User Query           Cached Results
               (WhatsApp)                │
                    │                    │
                    ▼                    │
              FastAPI Webhook            │
                    │                    │
                    ▼                    │
              RAG Pipeline ◄─────────────┘
              (Retrieve + Prompt)
                    │
                    ▼
              LLM Response
                    │
                    ▼
              WhatsApp Reply


naijahealth/
├── scraper/
│   ├── spiders/
│   │   ├── food.py
│   │   └── drugs.py
│   ├── parsers/
│   │   ├── food.py
│   │   └── drugs.py
│   ├── validators/
│   │   ├── food.py
│   │   └── drugs.py
│   └── runner.py
│
├── pipeline/
│   ├── embedder.py
│   ├── chunker.py
│   └── indexer.py
│
├── db/
│   ├── postgres/
│   │   ├── models.py
│   │   └── migrations/
│   ├── qdrant/
│   │   └── collections.py
│   └── redis/
│       └── cache.py
│
├── rag/
│   ├── retriever.py
│   ├── prompt.py
│   └── engine.py
│
├── bot/
│   ├── whatsapp/
│   │   ├── webhook.py
│   │   ├── handler.py
│   │   └── formatter.py
│   └── router.py
│
├── api/
│   ├── routes/
│   │   ├── health.py
│   │   └── query.py
│   └── main.py
│
├── scheduler/
│   └── jobs.py
│
├── core/
│   ├── config.py
│   └── logging.py
│
├── tests/
│   ├── scraper/
│   ├── rag/
│   └── bot/
│
├── docker/
│   ├── scraper.Dockerfile
│   └── api.Dockerfile
│
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md