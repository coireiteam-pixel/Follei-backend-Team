#!/bin/bash

# Navigate to the correct directory
cd /Users/balaa/follei_2/Follei-backend-Team/follei_backend/follei || exit

echo "🚀 Starting Docker containers (in detached mode)..."
docker compose up --build -d

echo "⏳ Waiting for the FastAPI backend to be healthy..."
# Ping the health endpoint every 2 seconds until it responds with HTTP 200 OK
until curl -s http://localhost:8000/health > /dev/null; do
  printf "."
  sleep 2
done

echo ""
echo "✅ Backend is up and running!"
echo "🌐 Opening Swagger UI in your default web browser..."
open http://localhost:8000/docs