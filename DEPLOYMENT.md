# HyDRA Deployment Guide

## Railway Deployment (Recommended)

HyDRA deploys as a single unified application on Railway, serving both the FastAPI backend and React frontend.

### Architecture

- **Platform**: Railway
- **Dockerfile**: Multi-stage build that compiles the React frontend and serves it via FastAPI
- **Frontend**: Built with Vite and served as static files from `/app/frontend/dist`
- **Backend**: FastAPI server handles API routes (`/api/*`) and serves the frontend for all other routes

### Required Environment Variables

Set these in your Railway dashboard:

```bash
OPENROUTER_API_KEY=your_api_key_here
ALLOWED_ORIGINS=https://your-railway-app.up.railway.app
SESSION_SECRET_KEY=your_secret_key_here
SESSION_MAX_AGE=7200  # Optional, defaults to 2 hours
```

### Deployment Steps

1. **Connect Repository to Railway**
   - Link your GitHub repository to Railway
   - Railway will auto-detect the `railway.toml` configuration

2. **Set Environment Variables**
   - Add required variables in Railway dashboard
   - Generate a secure SESSION_SECRET_KEY: `openssl rand -hex 32`

3. **Deploy**
   - Push to your main branch
   - Railway will automatically build and deploy
   - The app will be available at your Railway-provided URL

### Health Check

Railway monitors the `/api/health` endpoint to ensure the app is running properly.

### Local Development

For local development, run frontend and backend separately:

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

The Vite dev server will proxy API requests to `http://localhost:8000`.

### Troubleshooting

- **Build fails**: Check Railway logs for specific errors
- **Health check fails**: Ensure the app starts on Railway's `$PORT` variable
- **API not responding**: Verify `OPENROUTER_API_KEY` is set correctly
- **CORS errors**: Update `ALLOWED_ORIGINS` to include your Railway URL

### Migration from Vercel + Railway

Previously, HyDRA used:
- Vercel for frontend hosting
- Railway for backend API

Now everything runs on Railway for simplified deployment and management.
