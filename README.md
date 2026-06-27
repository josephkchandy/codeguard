# CodeGuard AI

AI-assisted Python repository bug analyzer.

## Stack

- Frontend: React + Vite
- Backend: FastAPI + LangGraph + Groq

## Local Run

Backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Environment

Backend `backend/.env`:

```env
GROQ_API_KEY=your_groq_key
```

Frontend `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Vercel Deployment

This repo includes `vercel.json` for deploying the Vite frontend from the `frontend/` folder.

In Vercel, set this environment variable:

```env
VITE_API_URL=https://your-deployed-backend-url
```

The FastAPI backend must be deployed separately unless you convert it to Vercel serverless functions. Good backend hosts include Render, Railway, Fly.io, or Azure App Service.
