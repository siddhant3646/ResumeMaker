# ResumeMaker AI - Hybrid Architecture Deployment Guide

This guide explains how to deploy the ResumeMaker AI application using the hybrid architecture with Vercel frontend and Streamlit backend.

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vercel (React Frontend)                       │
│  - Modern UI with Tailwind CSS                                   │
│  - Auth0 Authentication                                          │
│  - File Upload & Preview                                         │
│  - API calls to Streamlit Backend                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Streamlit Cloud / Render (Backend)                  │
│  - Resume Parsing                                                │
│  - AI Generation (NVIDIA API)                                    │
│  - ATS Scoring                                                   │
│  - PDF Rendering                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Options

### Option A: Streamlit Cloud (Recommended for Free Tier)

#### Step 1: Prepare Your Repository

1. Ensure your project structure includes the `streamlit_app/` directory
2. Push to GitHub

#### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set the main file path: `streamlit_app/app.py`
6. Click "Deploy"

#### Step 3: Configure Secrets

In the Streamlit Cloud dashboard, add these secrets:

```toml
NVIDIA_API_KEY = "your-nvidia-api-key-here"
```

#### Step 4: Update Frontend

Update `frontend/.env.production`:

```env
VITE_AUTH0_DOMAIN=dev-3r8bdikiiyz5vh18.us.auth0.com
VITE_AUTH0_CLIENT_ID=GqNoLYwCr2w58LSqkNGLnF6EbRouyvSe
VITE_STREAMLIT_BACKEND=true
VITE_API_URL=https://your-app-name.streamlit.app
```

#### Step 5: Deploy Frontend to Vercel

```bash
cd frontend
npm run build
vercel --prod
```

### Option B: Render (More Control)

#### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up and connect your GitHub

#### Step 2: Create Web Service

1. Click "New +" → "Web Service"
2. Connect your repository
3. Configure:
   - **Name:** resumemaker-streamlit
   - **Region:** Oregon (US West)
   - **Branch:** main
   - **Root Directory:** streamlit_app
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

#### Step 3: Add Environment Variables

- `NVIDIA_API_KEY`: Your NVIDIA API key
- `FRONTEND_URL`: Your Vercel frontend URL

#### Step 4: Deploy

Click "Create Web Service" and wait for deployment.

### Option C: Docker Deployment

#### Step 1: Build Docker Image

```bash
cd streamlit_app
docker build -t resumemaker-streamlit .
```

#### Step 2: Run Container

```bash
docker run -p 8501:8501 -e NVIDIA_API_KEY=your-key resumemaker-streamlit
```

#### Step 3: Deploy to Container Service

Deploy to any container hosting service:
- Google Cloud Run
- AWS ECS
- Azure Container Instances
- DigitalOcean App Platform

## 🔧 Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- NVIDIA API Key

### Setup Backend

```bash
# Navigate to streamlit app
cd streamlit_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY

# Run Streamlit
streamlit run app.py
```

### Setup Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file for Streamlit backend
cp .env.streamlit .env.local

# Run development server
npm run dev
```

### Test Integration

1. Open http://localhost:5173 (Frontend)
2. Open http://localhost:8501 (Streamlit Backend)
3. Upload a resume and test the workflow

## 🔐 Security Considerations

### CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (Development)
- `http://localhost:3000` (Alternative dev)
- `*.vercel.app` (Production frontends)

### API Key Security

- Never commit API keys to the repository
- Use environment variables or secrets management
- Rotate keys periodically

### Authentication

The frontend uses Auth0 for authentication. The backend validates tokens using JWT.

## 📊 Monitoring

### Health Check Endpoint

```bash
curl https://your-backend-url/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "service": "resumemaker-streamlit-backend"
}
```

### Logs

- **Streamlit Cloud:** View in the app dashboard
- **Render:** View in the service logs tab
- **Docker:** `docker logs <container-id>`

## 🐛 Troubleshooting

### Common Issues

#### 1. CORS Errors

**Symptom:** Frontend can't reach backend

**Solution:**
- Check `FRONTEND_URL` environment variable
- Verify CORS configuration in `api.py`
- Ensure frontend URL matches exactly

#### 2. API Key Not Found

**Symptom:** "NVIDIA_API_KEY not configured" error

**Solution:**
- Verify environment variable is set
- Check Streamlit secrets (for Streamlit Cloud)
- Restart the service after adding the key

#### 3. Cold Start Timeout

**Symptom:** First request times out

**Solution:**
- Increase frontend timeout
- Use a paid tier for always-on service
- Implement a warm-up mechanism

#### 4. PDF Upload Fails

**Symptom:** "Invalid PDF" error

**Solution:**
- Check file size (max 10MB)
- Verify PDF is not password protected
- Ensure PDF is not corrupted

## 📈 Performance Optimization

### Caching

Enable Redis caching for repeated requests:

```python
# In api.py
import redis

redis_client = redis.from_url(os.getenv('REDIS_URL'))
```

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/resume/generate", dependencies=[Depends(RateLimiter(times=10, minutes=1))])
async def generate_resume(...):
    ...
```

### Async Processing

For long-running operations, use background tasks:

```python
from fastapi import BackgroundTasks

@app.post("/api/resume/generate-async")
async def generate_resume_async(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_resume_generation)
    return {"status": "processing", "job_id": "..."}
```

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Streamlit Backend

on:
  push:
    branches: [main]
    paths:
      - 'streamlit_app/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl ${{ secrets.RENDER_DEPLOY_HOOK }}
```

## 📝 Next Steps

1. **Test the integration** locally first
2. **Deploy backend** to Streamlit Cloud or Render
3. **Update frontend** environment variables
4. **Deploy frontend** to Vercel
5. **Monitor** for any issues
6. **Optimize** based on usage patterns

## 🆘 Support

If you encounter issues:

1. Check the logs
2. Verify environment variables
3. Test API endpoints directly
4. Review CORS configuration
5. Open an issue on GitHub
