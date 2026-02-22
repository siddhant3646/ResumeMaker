# ResumeMaker AI - Production Deployment Guide

## 🚀 Quick Deployment (Recommended: Streamlit Cloud + Vercel)

This guide covers the fastest and easiest way to deploy the ResumeMaker AI application using free tier services.

### Prerequisites
1. GitHub account
2. NVIDIA API key (get from [NVIDIA Developer](https://developer.nvidia.com/))

---

## Step 1: Deploy Streamlit Backend to Streamlit Cloud

### 1.1 Push Code to GitHub
Make sure your repository is pushed to GitHub with the latest changes.

### 1.2 Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Configure your app:
   - **Repository:** Select your ResumeMaker repository
   - **Branch:** `main`
   - **Main file path:** `streamlit_app/app.py`
   - **App name:** Choose a unique name (e.g., `resumemaker-ai`)
5. Click **Deploy**

### 1.3 Configure Backend Secrets
1. Wait for the deployment to complete
2. Go to your app's **Settings** > **Secrets**
3. Add this secret:
   ```toml
   NVIDIA_API_KEY = "your-nvidia-api-key-here"
   ```
4. Click **Save**

### 1.4 Verify Backend
- Open your Streamlit app (e.g., `https://your-app-name.streamlit.app`)
- You should see the ResumeMaker AI backend interface

---

## Step 2: Deploy React Frontend to Vercel

### 2.1 Update Frontend Configuration
1. Open `frontend/.env.production`
2. Update the `VITE_API_URL` to your Streamlit app URL:
   ```env
   VITE_AUTH0_DOMAIN=dev-3r8bdikiiyz5vh18.us.auth0.com
   VITE_AUTH0_CLIENT_ID=GqNoLYwCr2w58LSqkNGLnF6EbRouyvSe
   VITE_API_URL=https://your-app-name.streamlit.app
   ```

### 2.2 Deploy to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **Add New Project**
3. Import your ResumeMaker repository
4. Configure project settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Click **Deploy**

### 2.3 Verify Frontend
- Open your Vercel app (e.g., `https://resumemaker-ai.vercel.app`)
- Test the application flow to ensure everything works

---

## Step 3: Test the Complete Application

### 3.1 Test the Workflow
1. Open your Vercel frontend app
2. Upload a resume PDF file
3. Enter a job description
4. Click **Generate Resume**
5. Verify that the Streamlit backend processes the request

### 3.2 Check Network Requests
- Open browser developer tools (F12)
- Go to **Network** tab
- Confirm all API requests are going to your Streamlit backend URL

---

## 🎉 Deployment Complete!

Your ResumeMaker AI application is now live!

**Access URLs:**
- Frontend: `https://your-vercel-app.vercel.app`
- Backend: `https://your-streamlit-app.streamlit.app`

---

## ⚠️ Important Notes

### 1. Cold Start Time
- Streamlit Cloud's free tier has cold start delays (up to 5 minutes)
- First request may time out - simply retry if this happens

### 2. Rate Limits
- Streamlit Cloud: 3 concurrent connections per app
- NVIDIA API: Check [API documentation](https://developer.nvidia.com/ai-foundation-models) for rate limits

### 3. Cost
- **Streamlit Cloud:** Free for most use cases
- **Vercel:** Free for hobby projects
- **NVIDIA API:** Free tier available with limits

---

## 🐛 Troubleshooting

### Common Issues

#### 1. CORS Errors
**Problem:** Frontend can't communicate with backend

**Solution:**
- Verify your Streamlit app URL in `frontend/.env.production`
- Check if your frontend domain is in the CORS allowed list in `streamlit_app/api.py`

#### 2. API Key Issues
**Problem:** "NVIDIA_API_KEY not configured" error

**Solution:**
- Check your Streamlit Cloud secrets
- Verify the API key is correctly entered in Secrets management

#### 3. Timeouts
**Problem:** Request takes too long

**Solution:**
- Try again (cold start issue)
- Consider upgrading to Streamlit Cloud's paid tier for faster access

---

## 📈 Monitoring

### Health Check
Test backend health:
```bash
curl https://your-streamlit-app.streamlit.app/api/health
```

**Expected Response:**
```json
{"status": "healthy", "version": "2.0.0", "service": "resumemaker-streamlit-backend"}
```

### Logs
- **Streamlit Cloud:** View in app dashboard > Manage app > Logs
- **Vercel:** View in project dashboard > Logs

---

## Next Steps

1. **Custom Domain:** Add custom domain to both frontend and backend
2. **Analytics:** Add Google Analytics or similar tracking
3. **Monitoring:** Set up error tracking and performance monitoring
4. **Scaling:** Consider upgrading to paid tiers for higher usage

---

## 🆘 Support

If you encounter issues:
1. Check the logs
2. Verify your configuration
3. Test API endpoints directly
4. Review CORS settings
5. Open an issue on GitHub
