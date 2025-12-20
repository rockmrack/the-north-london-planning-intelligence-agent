# Deployment Guide - Vercel

This guide covers deploying the North London Planning Intelligence Agent to Vercel.

## Architecture

The application is split into two parts:
- **Frontend**: Next.js 14 app (deployed to Vercel)
- **Backend**: FastAPI Python API (needs separate hosting)

## Frontend Deployment (Vercel)

### Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. Backend API deployed and accessible (see Backend Deployment section)
3. Git repository connected to Vercel

### Step 1: Connect Repository

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import your Git repository
4. Vercel will auto-detect the Next.js framework

### Step 2: Configure Build Settings

**IMPORTANT**: In the Vercel project settings, you MUST configure:

1. **Root Directory**: `frontend` (click "Edit" and set this to `frontend`)
2. **Framework Preset**: Next.js (auto-detected)
3. Leave other settings as default - Vercel will auto-detect:
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

The [vercel.json](vercel.json) file handles additional configuration (headers, regions, caching).

### Step 3: Environment Variables

Add these environment variables in Vercel Dashboard → Settings → Environment Variables:

#### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | Your backend API URL | Example: `https://your-api.railway.app` |

#### Optional Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_ENV` | `production` | Environment identifier |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | `true` | Enable analytics |
| `NEXT_PUBLIC_GA_ID` | Your GA ID | Google Analytics tracking ID |

See [frontend/.env.local.example](frontend/.env.local.example) for all available options.

### Step 4: Deploy

1. Click "Deploy"
2. Vercel will build and deploy automatically
3. You'll get a production URL like `https://your-project.vercel.app`

### Step 5: Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS as instructed by Vercel

## Backend Deployment

The FastAPI backend needs to be deployed separately. Recommended platforms:

### Option 1: Railway (Recommended)

1. Go to [Railway](https://railway.app)
2. Create new project from GitHub repo
3. Select the `backend` directory as root
4. Add environment variables from [.env.example](.env.example)
5. Deploy

Railway will auto-detect the Python app and deploy it.

### Option 2: Render

1. Go to [Render](https://render.com)
2. Create new Web Service
3. Connect your repository
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy

### Option 3: Google Cloud Run

1. Build Docker image from `backend/Dockerfile`
2. Push to Google Container Registry
3. Deploy to Cloud Run
4. Set environment variables
5. Enable public access

### Option 4: AWS Lambda (Serverless)

Use [Mangum](https://mangum.io/) to wrap the FastAPI app for Lambda:

```python
from mangum import Mangum
from app.main import app

handler = Mangum(app)
```

Deploy with AWS SAM or Serverless Framework.

## Required Backend Environment Variables

See [.env.example](.env.example) for the full list. Critical variables:

```bash
# Required
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
SECRET_KEY=your-secret-key

# CORS (add your Vercel domain)
BACKEND_CORS_ORIGINS=https://your-project.vercel.app,https://your-domain.com
```

## Testing the Deployment

1. Visit your Vercel URL
2. Open the chat widget
3. Ask a planning question
4. Verify the response comes from the backend

If you see errors:
- Check browser console for API errors
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend logs for errors
- Verify CORS is configured correctly

## Performance Optimizations

The deployment includes several optimizations:

### Frontend (Next.js)
- ✅ SWC minification enabled
- ✅ Image optimization with AVIF/WebP
- ✅ CSS optimization
- ✅ Package import optimization for common libraries
- ✅ Static asset caching (1 year)
- ✅ Font optimization
- ✅ Gzip compression

### Vercel Configuration
- ✅ London region (lhr1) for faster EU/UK access
- ✅ Security headers (CSP, XSS, Frame Options)
- ✅ Caching strategies for API and static content
- ✅ Telemetry disabled

### Backend
- Use Redis for caching (set `REDIS_URL`)
- Enable rate limiting
- Use CDN for static documents

## Monitoring

### Vercel Analytics
Enable in Vercel Dashboard → Analytics to track:
- Page views
- Performance metrics
- Web Vitals

### Backend Monitoring
Add to your backend environment:

```bash
SENTRY_DSN=your-sentry-dsn
ENABLE_METRICS=true
```

## Continuous Deployment

Vercel automatically deploys when you push to your main branch:
- **Production**: Pushes to `main` branch
- **Preview**: Pull requests get preview URLs

## Rollback

If a deployment fails:
1. Go to Vercel Dashboard → Deployments
2. Find the last working deployment
3. Click "..." → "Promote to Production"

## Cost Optimization

### Vercel
- Free tier supports:
  - 100GB bandwidth/month
  - Unlimited deployments
  - Hobby projects

### Backend
- Use serverless options (Lambda, Cloud Run) for low traffic
- Use Railway/Render for predictable costs
- Enable caching to reduce API calls
- Use free tier of Supabase for database

## Security Checklist

- [ ] Environment variables set in Vercel (not in code)
- [ ] CORS configured with your domain only
- [ ] API keys stored securely
- [ ] Security headers enabled (already configured)
- [ ] HTTPS enforced (automatic on Vercel)
- [ ] Rate limiting enabled on backend
- [ ] Input validation on all endpoints

## Troubleshooting

### 404 Errors
- Check `vercel.json` configuration
- Verify build completed successfully
- Check Vercel logs for build errors

### API Connection Errors
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend is running
- Verify CORS settings on backend
- Check network tab in browser DevTools

### Build Failures
- Check Node.js version (should be 18+)
- Verify all dependencies in `package.json`
- Check build logs in Vercel dashboard

### Slow Performance
- Enable caching on backend
- Check Vercel Analytics for bottlenecks
- Optimize images and assets
- Consider using CDN for static content

## Support

For issues:
1. Check Vercel deployment logs
2. Check backend logs
3. Review browser console errors
4. Check this repository's Issues section
