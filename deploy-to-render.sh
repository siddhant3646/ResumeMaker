#!/bin/bash
# Deploy Script for ResumeMaker to Render
# Usage: ./deploy-to-render.sh

set -e  # Exit on error

echo "🚀 ResumeMaker Deployment Script"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    print_error "app.py not found. Please run this script from the ResumeMaker directory."
    exit 1
fi

if [ ! -f "render.yaml" ]; then
    print_error "render.yaml not found. Please ensure you're in the correct directory."
    exit 1
fi

print_status "Step 1/10: Checking prerequisites..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

# Check if on correct branch
CURRENT_BRANCH=$(git branch --show-current)
print_status "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "feature/v2-resume-maker" ]; then
    print_warning "You're not on the feature/v2-resume-maker branch."
    read -p "Do you want to switch to feature/v2-resume-maker branch? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout feature/v2-resume-maker || {
            print_error "Failed to checkout branch. Please create it first with: git checkout -b feature/v2-resume-maker"
            exit 1
        }
        print_success "Switched to feature/v2-resume-maker branch"
    else
        print_warning "Continuing on $CURRENT_BRANCH branch..."
    fi
fi

print_status "Step 2/10: Checking GitHub remote..."

# Check if GitHub remote exists
if ! git remote -v > /dev/null 2>&1; then
    print_error "No GitHub remote configured."
    echo "Please add your GitHub remote:"
    echo "  git remote add origin https://github.com/siddhant3646/ResumeMaker.git"
    exit 1
fi

print_status "Step 3/10: Verifying all changes are committed..."

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes."
    git status --short
    echo ""
    read -p "Do you want to commit all changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " commit_msg
        git add -A
        git commit -m "$commit_msg"
        print_success "Changes committed"
    else
        print_error "Please commit or stash your changes before deploying."
        exit 1
    fi
else
    print_success "No uncommitted changes"
fi

print_status "Step 4/10: Pushing to GitHub..."

git push origin $(git branch --show-current) || {
    print_error "Failed to push to GitHub"
    exit 1
}

print_success "Code pushed to GitHub"

print_status "Step 5/10: Checking Auth0 configuration..."

echo ""
echo "=================================="
echo "🔐 Auth0 Setup Verification"
echo "=================================="
echo ""
echo "Please ensure you have:"
echo "1. Created an Auth0 account (auth0.com)"
echo "2. Created a new application"
echo "3. Set the following in Auth0 dashboard:"
echo "   - Allowed Callback URLs: https://your-app.onrender.com"
echo "   - Allowed Logout URLs: https://your-app.onrender.com"
echo "   - Allowed Web Origins: https://your-app.onrender.com"
echo ""

read -p "Have you completed Auth0 setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please complete Auth0 setup before continuing"
    echo "See DEPLOYMENT_GUIDE.md for detailed instructions"
    exit 1
fi

print_status "Step 6/10: Checking NVIDIA API key..."

if [ -z "$NVIDIA_API_KEY" ]; then
    print_warning "NVIDIA_API_KEY environment variable not set locally"
    echo "You'll need to add this to Render dashboard after deployment"
else
    print_success "NVIDIA_API_KEY is set"
fi

print_status "Step 7/10: Deployment preparation complete!"

echo ""
echo "=================================="
echo "📋 Next Steps - Manual Deployment"
echo "=================================="
echo ""
echo "Your code is now on GitHub. To complete deployment:"
echo ""
echo "1. Go to https://dashboard.render.com"
echo "2. Sign up/login with GitHub"
echo "3. Click 'New +' → 'Web Service'"
echo "4. Connect your GitHub repository: siddhant3646/ResumeMaker"
echo "5. Select branch: feature/v2-resume-maker"
echo "6. Render will auto-detect render.yaml"
echo "7. Add Environment Variables (see below)"
echo "8. Click 'Create Web Service'"
echo ""
echo "🔐 Required Environment Variables:"
echo "-----------------------------------"
echo "AUTH0_DOMAIN=your-domain.auth0.com"
echo "AUTH0_CLIENT_ID=your-client-id"
echo "AUTH0_CLIENT_SECRET=your-client-secret"
echo "AUTH0_REDIRECT_URI=https://ats-resume-maker.onrender.com"
echo "NVIDIA_API_KEY=your-nvidia-api-key"
echo ""
echo "Optional (for Redis/caching):"
echo "REDIS_URL=redis://..."
echo ""

print_status "Step 8/10: Would you like to open Render dashboard?"

read -p "Open Render dashboard in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open "https://dashboard.render.com"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "https://dashboard.render.com"
    else
        echo "Please open https://dashboard.render.com manually"
    fi
fi

print_status "Step 9/10: Post-deployment checklist..."

echo ""
echo "After deployment, verify:"
echo "□ Service is 'Live' (green dot)"
echo "□ No build errors in logs"
echo "□ Auth0 login works"
echo "□ Resume generation works"
echo "□ Mobile layout looks good"
echo ""

print_status "Step 10/10: Deployment process initiated!"

echo ""
echo "=================================="
echo "🎉 Deployment Summary"
echo "=================================="
echo ""
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git rev-parse --short HEAD)"
echo "GitHub: https://github.com/siddhant3646/ResumeMaker"
echo ""
echo "Next steps:"
echo "1. Go to Render dashboard"
echo "2. Complete environment variables"
echo "3. Deploy!"
echo ""
echo "For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo ""
print_success "Script completed successfully!"
