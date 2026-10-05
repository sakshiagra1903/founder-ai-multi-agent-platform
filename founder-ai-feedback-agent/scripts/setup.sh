#!/bin/bash
set -e
echo "🧠 Founder AI — Feedback Agent Setup"
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env — please add your GROQ_API_KEY then re-run"
  exit 1
fi
echo "Starting Docker services..."
docker-compose up --build -d
sleep 8
echo ""
echo "✅ Founder AI is running!"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Stop with: docker-compose down"
