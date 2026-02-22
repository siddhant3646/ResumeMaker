# ResumeMaker AI - Streamlit Backend

This is the Streamlit backend service for ResumeMaker AI, designed to work with the Vercel-hosted React frontend.

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Vercel        │   API   │   Streamlit     │
│   Frontend      │ ──────► │   Backend       │
│   (React)       │         │   (Python)      │
└─────────────────┘         └─────────────────┘
```

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your NVIDIA_API_KEY
   ```

3. **Run Streamlit app:**
   ```bash
   streamlit run app.py
   ```

4. **Run API server (separate terminal):**
   ```bash
   python api.py
   ```

### Streamlit Cloud Deployment

1. Push this directory to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the following secrets:
   - `NVIDIA_API_KEY`: Your NVIDIA API key

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Environment Variables:** `NVIDIA_API_KEY`

## 📁 Project Structure

```
streamlit_app/
├── app.py              # Main Streamlit application
├── api.py              # FastAPI wrapper for REST endpoints
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── config.toml     # Streamlit configuration
├── .env.example        # Environment variables template
└── README.md           # This file
```

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/resume/upload` | POST | Upload and parse resume PDF |
| `/api/resume/generate` | POST | Generate tailored resume |
| `/api/resume/score` | POST | Calculate ATS score |
| `/api/resume/render` | POST | Render resume as PDF |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NVIDIA_API_KEY` | NVIDIA AI API key | Yes |
| `FRONTEND_URL` | Frontend URL for CORS | No (default: localhost:5173) |

### Streamlit Secrets

For Streamlit Cloud, set secrets in the dashboard:

```toml
NVIDIA_API_KEY = "your-api-key-here"
```

## 🔌 Frontend Integration

Update your React frontend to point to the Streamlit backend:

```typescript
// frontend/src/services/api.ts
const API_URL = process.env.VITE_API_URL || 'http://localhost:8001';

export const uploadResume = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_URL}/api/resume/upload`, {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};
```

## 🧪 Testing

```bash
# Test API health
curl http://localhost:8001/api/health

# Test resume upload
curl -X POST http://localhost:8001/api/resume/upload \
  -F "file=@test_resume.pdf"
```

## 📝 Notes

- The Streamlit app provides a visual interface for testing
- The FastAPI wrapper (`api.py`) provides REST endpoints for the React frontend
- Both can run simultaneously on different ports

## 📄 License

MIT License
