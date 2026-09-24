# AI Presentation Generator v2

**AI-powered presentation generator built with Angular, Python, and Azure AI Foundry.**

Create presentations from a simple prompt or an uploaded document.

👉 **Try it:** https://ai-ppt-frontend.salmonpebble-6f51f89d.swedencentral.azurecontainerapps.io/prompt

```text
1. OUTLINE   →  AI plans what each slide should show
2. CONFIRM   →  You review / edit the plan
3. DESIGN    →  AI generates each slide independently
4. PRESENT   →  Present fullscreen while reading your notes * 🔒 Your notes are not included in the shared presentation screen

5. EXPORT    →  PPTX or HTML
```

## Project structure

```text
ai-ppt-generator/
├── backend/                 # Python / FastAPI
│   ├── app/
│   │   ├── main.py          # API routes
│   │   ├── config.py
│   │   ├── models.py
│   │   └── services/
│   │       ├── llm.py       # AI generation
│   │       ├── parser.py
│   │       └── exporter.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                # Angular application
│   ├── src/
│   ├── angular.json
│   ├── package.json
│   └── ...
│
├── Dockerfile
└── README.md
```

## Technologies

| Part       | Technologies                                                     |
| ---------- | ---------------------------------------------------------------- |
| Frontend   | Angular, TypeScript, HTML, CSS                                   |
| Backend    | Python, FastAPI                                                  |
| AI         | Azure AI Foundry, Gemini, Groq, OpenRouter, Ollama, Hugging Face |
| Deployment | Microsoft Azure, Azure Container Apps, Docker                    |
| Registry   | Azure Container Registry                                         |

## Two-phase flow

| Step | What happens                                          |
| ---- | ----------------------------------------------------- |
| 1    | AI creates a structured presentation outline          |
| 2    | You review and edit the slides                        |
| 3    | AI generates the design of each slide independently   |
| 4    | Present the slides in fullscreen with presenter notes |
| 5    | Export the presentation as PPTX or HTML               |

## AI Models

The project supports multiple AI providers and can use models available through **Azure AI Foundry**, as well as other providers such as Gemini, Groq, OpenRouter, Ollama, and Hugging Face.

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

uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Health:

```text
http://127.0.0.1:8000/api/health
```

### 2. Frontend

```bash
cd frontend
npm install
ng serve
```

Open:

```text
http://localhost:4200
```

## Azure

The application is deployed on **Microsoft Azure** using **Azure Container Apps**.

The backend uses AI models through **Azure AI Foundry**, while the Angular frontend is deployed separately.

```text
Angular
   │
   ▼
Azure Container Apps
   │
   ▼
Python / FastAPI
   │
   ▼
Azure AI Foundry
   │
   ▼
AI Models
```

## Live Demo

**https://ai-ppt-frontend.salmonpebble-6f51f89d.swedencentral.azurecontainerapps.io/prompt**
