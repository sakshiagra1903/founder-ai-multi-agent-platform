README 

# Founder AI — Complete Multi-Agent System

This zip contains 4 things, kept together:
```
founder-ai-feedback-agent/   ← your original Feedback Agent (completely unchanged)
founder-ai-final/            ← your original Hiring Agent (completely unchanged)
support_agent/                ← your original Support Agent (completely unchanged)
orchestrator/                 ← NEW — the routing layer that integrates them
docker-compose.yml            ← NEW — runs everything together on non-conflicting ports
```


Not a single line was changed inside the original agents — same code, same DB models, same auth, same RAG pipelines, same tools.

## Setup 

### 1. Create a `.env` for each agent 
```bash
cd founder-ai-feedback-agent/backend && cp .env.example .env   # add your Groq/OpenAI key
cd ../../founder-ai-final/backend      && cp .env.example .env   # add your Groq/OpenAI key
cd ../../support_agent                 && cp .env.example .env   # add your Groq/OpenAI key
```


### 2. Create the orchestrator's `.env`
```bash
cd ../orchestrator
cp .env.example .env
```
Open `.env` and put your Groq key in `GROQ_API_KEY=` 

### 3. Run everything together
From the root folder 
```bash
docker compose up --build
```
The first build will take a little time since images need to build.

## What runs where

 Service 
 Orchestrator  http://localhost:8000 
 Feedback backend  http://localhost:8001 
 Hiring backend  http://localhost:8002 
 Support backend http://localhost:8003 
 Feedback frontend  http://localhost:3001 
 Hiring frontend  http://localhost:3002 
 Support frontend  http://localhost:3003 

 How to test

1. Go to any agent's frontend (3001/3002/3003) and sign up/log in normally — just like before.
2. Send the JWT token you got from that login to the orchestrator:
bash

The orchestrator will decide on its own whether this question belongs to support/feedback/hiring, and will call that agent's existing backend to get the answer.

For full details, see `orchestrator/README.md`.





## Windows / PowerShell — easiest run

1. Open this folder in VS Code.
2. Open `/.env` and replace:
   `PASTE_YOUR_GROQ_API_KEY_HERE`
   with your Groq API key.
3. Make sure Docker Desktop is running.
4. In PowerShell, from this folder run:

```powershell
docker compose down -v
docker compose up --build -d
```

5. Check containers:

```powershell
docker compose ps
docker compose logs -f orchestrator
```

6. Open the main frontend:
   `http://localhost:8000`

The upgraded package now uses the orchestrator's built-in frontend at port 8000.
The specialist frontends are also available:
- Feedback: http://localhost:3001
- Hiring: http://localhost:3002
- Support: http://localhost:3003

Backends:
- Orchestrator: http://localhost:8000
- Feedback: http://localhost:8001
- Hiring: http://localhost:8002
- Support: http://localhost:8003

Health checks:
- http://localhost:8000/health
- http://localhost:8000/api/agents/health

### Important
The root `docker-compose.yml` no longer requires four missing `.env` files inside the individual projects. All four services receive the shared Groq key from the root `/.env`.

If a container already exists with an old conflicting name, run:

```powershell
docker compose down -v --remove-orphans
docker compose up --build -d
```

Do not run the three original agents' individual `docker-compose.yml` files at the same time, because those files publish overlapping host ports such as 8000/5432/6379. Use the root `docker-compose.yml` for the complete system.
