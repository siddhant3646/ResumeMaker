# Complete Deployment Guide - ResumeMaker on Render

This guide will walk you through deploying ResumeMaker to Render's free tier.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Step 1: Auth0 Setup](#step-1-auth0-setup)
3. [Step 2: Push Code to GitHub](#step-2-push-code-to-github)
4. [Step 3: Create Render Account](#step-3-create-render-account)
5. [Step 4: Deploy to Render](#step-4-deploy-to-render)
6. [Step 5: Configure Environment Variables](#step-5-configure-environment-variables)
7. [Step 6: Update Auth0 URLs](#step-6-update-auth0-urls)
8. [Step 7: Verify Deployment](#step-7-verify-deployment)
9. [Step 8: Optional - Setup Redis](#step-8-optional---setup-redis)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before you start, ensure you have:

- [ ] GitHub account
- [ ] Auth0 account (free tier)
- [ ] NVIDIA API key (from NVIDIA NGC)
- [ ] Code pushed to `feature/v2-resume-maker` branch

---

## Step 1: Auth0 Setup

### 1.1 Create Auth0 Account
1. Go to [auth0.com](https://auth0.com)
2. Sign up for free account
3. Verify your email

### 1.2 Create Application
1. In Auth0 Dashboard, click "Applications" → "Create Application"
2. Name: `ATS Resume Maker`
3. Type: `Regular Web Application`
4. Click "Create"

### 1.3 Configure Application Settings
1. Go to "Settings" tab
2. Find "Application URIs" section
3. For now, set these (we'll update after Render deployment):
   - Allowed Callback URLs: `http://localhost:8501`
   - Allowed Logout URLs: `http://localhost:8501`
   - Allowed Web Origins: `http://localhost:8501`
4. Save changes

### 1.4 Get Credentials
1. In Settings tab, copy these values:
   - **Domain**: `your-domain.auth0.com`
   - **Client ID**: long string
   - **Client Secret**: click "Reveal" to see it
2. Save these securely - you'll need them later

---

## Step 2: Push Code to GitHub

### 2.1 Ensure You're on Correct Branch
```bash
cd /path/to/ResumeMaker
git branch
# Should show: feature/v2-resume-maker
```

### 2.2 Commit Any Pending Changes
```bash
git add -A
git commit -m "Ready for deployment"
```

### 2.3 Push to GitHub
```bash
git push origin feature/v2-resume-maker
```

### 2.4 Verify on GitHub
1. Go to https://github.com/siddhant3646/ResumeMaker
2. Check that `feature/v2-resume-maker` branch exists
3. Verify recent commits are there

---

## Step 3: Create Render Account

### 3.1 Sign Up
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "Get Started"
3. Choose "Sign up with GitHub"
4. Authorize Render to access your repositories

### 3.2 Verify Email
1. Check your email for verification link
2. Click to verify

---

## Step 4: Deploy to Render

### 4.1 Create New Web Service
1. In Render Dashboard, click "New +"
2. Select "Web Service"

### 4.2 Connect Repository
1. Find and select: `siddhant3646/ResumeMaker`
2. Click "Connect"

### 4.3 Configure Service
Fill in these details:

| Field | Value |
|-------|-------|
| Name | `ats-resume-maker` |
| Region | Select closest to your users (e.g., Oregon) |
| Branch | `feature/v2-resume-maker` |
| Runtime | `Docker` |
| Plan | `Free` |

### 4.4 Advanced Settings (optional)
- Disk: Leave default
- Health Check Path: `/_stcore/health`

### 4.5 Create Service
Click "Create Web Service"

**Wait for initial build (2-3 minutes)**

---

## Step 5: Configure Environment Variables

### 5.1 Open Environment Tab
1. In your service dashboard, click "Environment" tab
2. Click "Add Environment Variable"

### 5.2 Add Required Variables

Add these one by one:

```
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id-from-auth0
AUTH0_CLIENT_SECRET=your-client-secret-from-auth0
AUTH0_REDIRECT_URI=https://ats-resume-maker.onrender.com
NVIDIA_API_KEY=your-nvidia-api-key
```

### 5.3 Optional Variables (for scaling)
```
REDIS_URL=your-redis-url (if using Upstash)
UPSTASH_REDIS_REST_URL=your-upstash-url
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
```

### 5.4 Save Changes
Click "Save Changes"

**Render will automatically redeploy with new variables**

---

## Step 6: Update Auth0 URLs

### 6.1 Get Render URL
1. In Render dashboard, find your service URL
2. It looks like: `https://ats-resume-maker.onrender.com`

### 6.2 Update Auth0 Settings
1. Go back to Auth0 Dashboard
2. Select your application
3. Go to "Settings" tab
4. Update these URLs (replace with your actual Render URL):

```
Allowed Callback URLs: https://ats-resume-maker.onrender.com
Allowed Logout URLs: https://ats-resume-maker.onrender.com  
Allowed Web Origins: https://ats-resume-maker.onrender.com
```

5. **Save Changes**

---

## Step 7: Verify Deployment

### 7.1 Check Service Status
1. In Render dashboard, look for green dot (Live)
2. Click URL to open app

### 7.2 Test Login
1. Open your app URL
2. Click "Sign in with Google" or "Sign in with GitHub"
3. Should redirect to Auth0, then back to app
4. You should see your name in header

### 7.3 Test Resume Generation
1. Upload a resume PDF
2. Choose mode (ATS-Only or Tailor for Job)
3. Click "Tailor Resume"
4. Should see progress bar and get result

### 7.4 Test Editor
1. After generation, click "Edit Resume"
2. Try editing a bullet point
3. Try AI improvement with custom prompt

### 7.5 Test Mobile
1. Open app on phone
2. Verify layout looks good
3. Test upload and generation

---

## Step 8: Optional - Setup Redis

For better performance with 5000 users, set up Redis (free tier).

### 8.1 Sign up for Upstash
1. Go to [upstash.com](https://upstash.com)
2. Sign up with GitHub
3. Create new Redis database
4. Select region (same as Render)

### 8.2 Get Connection Details
1. In Upstash console, go to "Details" tab
2. Copy:
   - REST URL
   - REST Token

### 8.3 Add to Render
1. Go back to Render environment variables
2. Add:
```
UPSTASH_REDIS_REST_URL=https://your-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token
```
3. Save and redeploy

---

## Troubleshooting

### Issue: Build Fails
**Solution:**
1. Check build logs in Render dashboard
2. Common issues:
   - Missing requirements: Check `requirements.txt`
   - Import errors: Ensure all new files are committed
3. Try rebuilding: Click "Manual Deploy" → "Deploy latest commit"

### Issue: Auth0 Login Not Working
**Solution:**
1. Check environment variables are set correctly
2. Verify Auth0 URLs match your Render URL exactly
3. Check Auth0 logs in Auth0 dashboard
4. Common mistakes:
   - Trailing slash in URL
   - Wrong domain format (should be `domain.auth0.com`)
   - Client Secret not copied correctly

### Issue: Resume Generation Times Out
**Solution:**
1. Check NVIDIA_API_KEY is valid
2. Test API key locally first
3. Check Render logs for error messages
4. May need to upgrade Mistral tier if hitting rate limits

### Issue: "Processing..." Button Stuck
**Solution:**
1. Refresh page (ProcessingGuard should reset)
2. Check if you clicked button twice rapidly
3. Clear browser cache and try again

### Issue: Mobile Layout Broken
**Solution:**
1. Check that `ui/themes.py` changes are deployed
2. Clear browser cache
3. Test in incognito mode

### Issue: Redis Connection Errors
**Solution:**
1. Check UPSTASH_REDIS_REST_URL format (should start with https://)
2. Verify token is complete (no extra spaces)
3. Test Redis connection separately

---

## Monitoring & Maintenance

### View Logs
1. In Render dashboard, click "Logs" tab
2. See real-time application logs
3. Filter by type (Deploy, Runtime, etc.)

### Check Usage
1. Free tier includes:
   - 512MB RAM
   - Shared CPU
   - 100GB bandwidth/month
2. Monitor in Render dashboard

### Scale Up (if needed)
If you exceed free tier limits:
1. Go to "Settings" tab
2. Change Plan to "Starter" ($7/month)
3. More RAM and dedicated CPU

---

## Quick Commands

### Check Deployment Status
```bash
# View recent commits
git log --oneline -5

# Check branch
git branch

# View uncommitted changes
git status
```

### Redeploy
In Render dashboard:
1. Go to your service
2. Click "Manual Deploy"
3. Select "Deploy latest commit"

### Rollback
If something breaks:
1. In Render dashboard
2. Click "Manual Deploy"
3. Select previous commit from dropdown

---

## Success Checklist

After deployment, verify:

- [ ] App loads at Render URL
- [ ] Auth0 login works
- [ ] Can upload resume
- [ ] Can generate tailored resume
- [ ] Can edit resume with AI
- [ ] Mobile layout works
- [ ] Download PDF works
- [ ] No console errors in browser
- [ ] Logs show no errors

---

## Support

If you encounter issues:

1. **Render Issues:** [render.com/docs](https://render.com/docs)
2. **Auth0 Issues:** [auth0.com/docs](https://auth0.com/docs)
3. **App Issues:** Check logs in Render dashboard

---

## Next Steps After Deployment

1. **Custom Domain** (optional):
   - In Render: Settings → Custom Domain
   - Add your domain
   - Update Auth0 URLs

2. **Monitoring** (optional):
   - Set up uptime monitoring
   - Configure alerts

3. **Analytics** (optional):
   - Track user signups
   - Monitor API usage

---

**🎉 You're now ready to deploy! Good luck!**
