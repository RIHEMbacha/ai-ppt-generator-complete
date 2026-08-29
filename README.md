# AI Presentation Generator v2

**Two-phase AI presentation system** (backend + frontend)

```
1. OUTLINE   →  AI plans what each slide should show
2. CONFIRM   →  You review / edit the plan
3. DESIGN    →  AI generates HTML for each slide independently
4. EXPORT    →  PPTX or HTML
```

## Project structure

```
ai-ppt-generator/
├── backend/                 # FastAPI (Python)
│   ├── app/
│   │   ├── main.py          # API routes
│   │   ├── config.py
│   │   ├── models.py
│   │   └── services/
│   │       ├── llm.py       # Outline agent + per-slide HTML agent (with retries)
│   │       ├── parser.py
│   │       └── exporter.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Static SPA (no build step)
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
└── README.md
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env .env     # Windows  (or: cp .env .env)

# Edit .env:
#   LLM_PROVIDER=gemini
#   GEMINI_API_KEY=AIzaSy...     ← must start with AIza
#   GEMINI_MODEL=gemini-2.5-flash
#   CORS_ORIGINS=http://localhost:3000,http://localhost:4200

uvicorn app.main:app --reload --port 8000
```

Backend: http://127.0.0.1:8000  
Health:  http://127.0.0.1:8000/api/health

### 2. Frontend

```bash
cd frontend
python -m http.server 3000
```

Open: **http://localhost:3000**

## Two-phase flow

| Step | Endpoint | What happens |
|------|----------|--------------|
| 1 | POST /api/outline | AI creates content plan (no HTML yet) |
| 2 | (UI) | You edit labels, content, order |
| 3 | POST /api/generate-html | One independent design prompt per slide + auto-retry |
| 4 | POST /api/export | Download PPTX or HTML |

## LLM providers

| Provider | Env key | Notes |
|----------|---------|-------|
| gemini (recommended) | GEMINI_API_KEY | Best free quality |
| groq | GROQ_API_KEY | Very fast |
| ollama | local | Fully offline |
| huggingface | HF_TOKEN | Free, smaller models |

Get Gemini key: https://aistudio.google.com/app/apikey (must start with AIza)
