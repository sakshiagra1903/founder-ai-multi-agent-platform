# 🤖 Founder AI — Multi-Agent Startup Operating System

> An AI-powered multi-agent platform designed to help startup teams manage customer support, hiring, and feedback workflows through specialized AI agents coordinated by a central orchestrator.

## 🚀 Overview

Founder AI is a modular **Multi-Agent AI Platform** where different AI agents handle different startup operations.

Instead of using one large AI system for everything, the platform separates responsibilities into specialized agents:

- 🎧 **Support Agent** — Handles customer/support-related workflows
- 👥 **Hiring Agent** — Assists with hiring-related workflows
- 💬 **Feedback Agent** — Processes feedback-related workflows
- 🧠 **Orchestrator** — Coordinates requests and routes them to the appropriate agent

The goal is to provide an AI-powered operating layer for common startup workflows using a modular multi-agent architecture.

---

## 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │       Frontend       │
                         │   User Interaction   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Orchestrator     │
                         │  Request Routing &   │
                         │  Agent Coordination  │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │   Support    │  │   Hiring     │  │   Feedback   │
          │    Agent     │  │    Agent     │  │    Agent     │
          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │      AI / LLM        │
                         │  Agent Intelligence  │
                         └──────────────────────┘
```

---

## ✨ Key Features

### 🧠 Multi-Agent Architecture

The system uses specialized AI agents for different startup functions instead of relying on one monolithic assistant.

### 🎯 Intelligent Request Routing

The Orchestrator acts as the central coordination layer and routes requests to the appropriate agent.

### 🎧 Support Automation

The Support Agent is designed to handle support-oriented interactions and workflows.

### 👥 Hiring Assistance

The Hiring Agent provides AI-powered assistance for hiring-related tasks.

### 💬 Feedback Processing

The Feedback Agent handles feedback-related workflows and transforms input into useful information.

### 🧩 Modular Design

Each major agent is separated into its own service, making the platform easier to maintain and extend.

### 🐳 Dockerized Setup

The project includes Docker and Docker Compose configuration for running multiple services together.

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- REST APIs
- Pydantic

## AI / LLM

- Groq-compatible LLM integration
- Multi-Agent Architecture
- Prompt-based AI workflows

## Frontend

- Next.js
- React
- TypeScript
- HTML / CSS

## Database & Storage

- PostgreSQL
- Redis
- ChromaDB

## Infrastructure

- Docker
- Docker Compose

---

# 📁 Project Structure

```text
founder-ai-runnable/
│
├── founder-ai-feedback-agent/
│   └── backend/
│       └── Feedback Agent
│
├── founder-ai-final/
│   ├── backend/
│   │   └── Hiring Agent
│   └── frontend/
│
├── orchestrator/
│   └── Orchestrator Service
│
├── support_agent/
│   ├── backend/
│   │   └── Support Agent
│   └── frontend/
│
├── chat_models.py
├── docker-compose.yml
├── orchestrator-console.html
├── .env.example
└── README.md
```

---

# 🔄 How It Works

```text
User Request
     │
     ▼
  Frontend
     │
     ▼
Orchestrator
     │
     ├──────────────► Support Agent
     │
     ├──────────────► Hiring Agent
     │
     └──────────────► Feedback Agent
                         │
                         ▼
                    AI Processing
                         │
                         ▼
                      Response
                         │
                         ▼
                        User
```

### 1. User Request

The user sends a request through the application interface.

### 2. Orchestrator

The Orchestrator receives the request and coordinates the workflow.

### 3. Agent Selection

The request is routed to the appropriate specialized agent.

### 4. AI Processing

The selected agent processes the request using the configured AI/LLM workflow.

### 5. Response

The final response is returned to the user through the application.

---

# ⚙️ Getting Started

## Prerequisites

Make sure you have:

- Python
- Docker Desktop
- Docker Compose
- Node.js
- Git

installed on your system.

---

## 1. Clone the Repository

```bash
git clone https://github.com/sakshiagra1903/founder-ai-multi-agent-platform.git
```

Move into the project:

```bash
cd founder-ai-multi-agent-platform
```

---

## 2. Configure Environment Variables

The repository contains `.env.example` files as configuration templates.

Create your local `.env` file from the example:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Then add your own API credentials.

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> ⚠️ Never commit real API keys or `.env` files to GitHub.

---

# 🐳 Running with Docker

Make sure Docker Desktop is running.

### Build the services

```bash
docker compose build
```

### Start the application

```bash
docker compose up
```

### Run in background

```bash
docker compose up -d
```

### Stop the application

```bash
docker compose down
```

### Rebuild from scratch

```bash
docker compose build --no-cache
docker compose up
```

---

# 🔐 Environment Variables

Sensitive credentials should be stored locally.

The repository only contains example configuration files.

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
```

**Do not upload your real API key to GitHub.**

---

# 🧪 Development Workflow

A typical development workflow is:

```text
Modify Agent
     │
     ▼
Run Service
     │
     ▼
Test API
     │
     ▼
Test Frontend
     │
     ▼
Test Through Orchestrator
```

Each agent can be developed and tested independently while the Orchestrator provides the central coordination layer.

---

# 📌 Available Agents

| Agent | Responsibility |
|---|---|
| 🧠 Orchestrator | Coordinates and routes requests |
| 🎧 Support Agent | Support-related workflows |
| 👥 Hiring Agent | Hiring-related workflows |
| 💬 Feedback Agent | Feedback-related workflows |

---

# 🔮 Future Improvements

The architecture can be extended with additional specialized agents:

- 📅 Meeting Agent
- 📊 Analytics Agent
- 📢 Marketing Agent
- 💰 Finance Agent
- 📋 Task Management Agent
- 📧 Email Agent
- 📄 Document Processing Agent

Potential future improvements include:

- Agent memory
- Advanced RAG pipelines
- Role-Based Access Control
- Authentication and authorization
- Agent monitoring and observability
- Agent evaluation
- Human-in-the-loop workflows
- Cloud deployment
- Production-grade logging

---

# 🎯 Why Multi-Agent AI?

Startups have many different repetitive workflows.

A multi-agent architecture allows each AI agent to specialize in a particular business function.

```text
                    Founder AI
                        │
                        ▼
                  Orchestrator
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Support        Hiring       Feedback
        Agent          Agent         Agent
```

This approach makes the platform:

- Modular
- Extensible
- Easier to maintain
- Easier to test
- Easier to expand with new agents

---

# 📊 Project Highlights

### Architecture

- Multi-Agent System
- Central Orchestration Layer
- Modular Agent Services
- Service-based architecture

### AI

- LLM-powered workflows
- Specialized AI agents
- Prompt-based task processing

### Software Engineering

- REST APIs
- Dockerized services
- Frontend/backend separation
- Environment-based configuration
- Modular project structure

---

# 👩‍💻 Author

## Sakshi Agrawal

**B.Tech — Artificial Intelligence & Machine Learning**

### GitHub

https://github.com/sakshiagra1903


---

# ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

---

# 📜 License

This project is intended for educational, development, and demonstration purposes.
## 🎥 Project Demo

A complete demonstration of the Founder AI Multi-Agent Platform.

> The demo showcases the multi-agent architecture, orchestrator, and specialized Support, Hiring, and Feedback agents.

🎬 **Project Demo Video:**  
[Watch the Founder AI Demo](./WhatsApp%20Video%202026-10-04%20at%208.55.35%20PM.mp4)
