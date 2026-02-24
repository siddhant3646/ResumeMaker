# ResumeMaker AI - Streamlit Application

A comprehensive AI-powered resume builder built with Streamlit. Upload your resume, tailor it for specific job descriptions, and download ATS-optimized PDFs.

## Features

- 📤 **Resume Upload** - Upload and parse PDF resumes
- 🎯 **AI Tailoring** - Generate resumes optimized for specific job descriptions
- 📊 **ATS Scoring** - Get ATS compatibility scores
- 📝 **Resume Editor** - View and edit generated resumes
- 🔒 **Password Protection** - Secure access with password authentication
- 🎨 **Modern UI** - Beautiful dark theme with custom styling

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/resumemaker.git
   cd resumemaker/streamlit_app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your NVIDIA_API_KEY
   ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Deployment to Streamlit Cloud

### Step 1: Push to GitHub

Make sure your repository is pushed to GitHub with the latest changes.

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Configure:
   - **Repository:** Select your ResumeMaker repository
   - **Branch:** `main`
   - **Main file path:** `streamlit_app/app.py`
5. Click **Deploy**

### Step 3: Configure Secrets

In the Streamlit Cloud dashboard:

1. Go to your app's **Settings** > **Secrets**
2. Add these secrets:
   ```toml
   NVIDIA_API_KEY = "your-nvidia-api-key-here"
   APP_PASSWORD = "your-password-here"
   ```
3. Click **Save**

### Step 4: Access Your App

Your app will be available at: `https://your-app-name.streamlit.app`

**Password:** You must set `APP_PASSWORD` in Streamlit secrets. There is no default password in production.

For local development with `STREAMLIT_ENV=development`, the password is `dev-password`.

## Project Structure

```
streamlit_app/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── backend/                  # Backend modules
│   ├── __init__.py
│   └── app/
│       ├── __init__.py
│       ├── models.py
│       ├── resume.py
│       └── ai_client.py
├── intelligence/             # AI modules
│   ├── __init__.py
│   ├── ats_scorer.py
│   ├── content_generator.py
│   └── role_detector.py
└── vision/                   # PDF validation
    ├── __init__.py
    └── pdf_validator.py
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NVIDIA_API_KEY` | NVIDIA API key for AI features | Yes |
| `APP_PASSWORD` | Password for app access | Yes (no default in production) |

### Streamlit Secrets

Set these in the Streamlit Cloud dashboard:

```toml
NVIDIA_API_KEY = "your-key"
APP_PASSWORD = "your-password"
```

## Usage

1. **Login** - Enter the app password
2. **Upload Resume** - Upload your existing resume PDF
3. **Generate** - Paste job description and generate tailored resume
4. **Edit** - Review and modify the generated content
5. **Download** - Download the ATS-optimized PDF

## API Keys

### NVIDIA API Key

1. Go to [NVIDIA Developer](https://developer.nvidia.com/)
2. Sign up/Login
3. Generate an API key
4. Add to Streamlit secrets

## Troubleshooting

### Import Errors

If you see import errors, ensure all modules are in the `streamlit_app/` directory:
- `backend/`
- `intelligence/`
- `vision/`

### API Key Issues

If AI features don't work:
1. Check that `NVIDIA_API_KEY` is set in secrets
2. Verify the key is valid
3. Check Streamlit logs for errors

### PDF Generation Issues

If PDF generation fails:
1. Ensure `fpdf2` is installed
2. Check that resume data is valid
3. Try regenerating the resume

## License

MIT License - See LICENSE file for details.
