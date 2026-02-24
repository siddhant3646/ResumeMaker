# Vercel Serverless Backend Deployment Plan

## Overview

Deploy the FastAPI backend as Vercel Serverless Functions alongside the React frontend. This approach:
- Keeps everything in one Vercel project
- Uses free tier effectively (100 GB bandwidth, millions of execution seconds)
- No cold start issues for typical resume processing times

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Vercel Deployment                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   React Frontend    │    │    Python Serverless Functions  │ │
│  │   (Static Files)    │    │    (FastAPI Endpoints)          │ │
│  │                     │    │                                  │ │
│  │   /                 │    │    /api/health                  │ │
│  │   /editor           │    │    /api/resume/upload           │ │
│  │   /upload           │    │    /api/resume/generate         │ │
│  │                     │    │    /api/resume/download         │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure Changes

```
ResumeMaker/
├── api/                          # NEW: Vercel Python serverless functions
│   ├── index.py                  # Main FastAPI entry point
│   ├── requirements.txt          # Python dependencies for Vercel
│   ├── backend/                  # Copied backend modules
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── resume.py
│   │       └── ai_client.py
│   ├── intelligence/             # Copied intelligence modules
│   │   ├── __init__.py
│   │   ├── ats_scorer.py
│   │   ├── content_generator.py
│   │   └── role_detector.py
│   └── vision/                   # Copied vision modules
│       ├── __init__.py
│       └── pdf_validator.py
├── frontend/                     # React frontend (unchanged)
│   ├── src/
│   ├── package.json
│   └── vercel.json
├── vercel.json                   # UPDATED: Root Vercel config
└── ... other files
```

## Implementation Steps

### Step 1: Create API Directory Structure

Create `api/` directory at project root with all necessary Python modules.

### Step 2: Create Vercel Python Entry Point

Create `api/index.py` that exports a FastAPI app. Vercel automatically detects this.

### Step 3: Update Root vercel.json

Configure Vercel to:
- Build frontend from `frontend/` directory
- Serve Python functions from `api/` directory
- Route `/api/*` requests to Python functions

### Step 4: Update Frontend API URL

Update `frontend/.env.production` to use relative API paths:
```
VITE_API_URL=
```

This makes the frontend call `/api/*` endpoints on the same domain.

## Key Configuration Files

### vercel.json (Root)
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "functions": {
    "api/index.py": {
      "runtime": "python3.11"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/index.py"
    },
    {
      "source": "/((?!api/).*)",
      "destination": "/frontend/index.html"
    }
  ]
}
```

### api/requirements.txt
```
fastapi
python-multipart
fpdf2
pypdf
pdfplumber
Pillow
google-generativeai
pydantic>=2.0.0
python-dotenv
requests
beautifulsoup4
httpx
aiohttp
jinja2
tenacity
PyJWT
```

## Limitations to Consider

1. **No WebSockets** - Vercel serverless doesn't support WebSocket connections
   - Solution: Remove WebSocket functionality or use polling instead

2. **No Background Tasks** - FastAPI BackgroundTasks won't work reliably
   - Solution: Process everything synchronously within the request

3. **Execution Time Limit** - 10 seconds on Hobby plan, 60 seconds on Pro
   - Solution: Optimize AI calls or upgrade to Pro plan

4. **Cold Starts** - First request may be slower
   - Solution: Accept this limitation for typical usage patterns

## Deployment Steps

1. Push changes to GitHub
2. Connect repository to Vercel
3. Vercel auto-detects configuration
4. Set environment variables in Vercel dashboard:
   - `NVIDIA_API_KEY`
5. Deploy!

## Alternative: Separate Projects

If you prefer separate Vercel projects:
- Frontend: Deploy `frontend/` as one Vercel project
- Backend: Deploy `api/` as another Vercel project
- Update `VITE_API_URL` to point to backend project URL
