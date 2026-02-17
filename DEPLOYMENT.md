# HyDRA Deployment Guide

## Quick Start - Deploy to Railway

### 1. Push Your Code
```bash
git push
```

### 2. Configure Railway

1. **Go to [Railway.app](https://railway.app)** and sign in
2. **Create a New Project** → Select "Deploy from GitHub repo"
3. **Connect your HyDRA repository**
4. Railway will auto-detect the `railway.toml` and `Dockerfile`

### 3. Set Environment Variables

In your Railway project dashboard, go to **Variables** and add:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Generate a secure key (run: openssl rand -hex 32)
SESSION_SECRET_KEY=your-64-character-hex-key-here

# Optional - Add these if needed
SESSION_MAX_AGE=7200
OPENROUTER_MODEL=anthropic/claude-sonnet-4
```

**Note:** Don't set `ALLOWED_ORIGINS` yet - you'll add it after deployment when you see your Railway URL.

### 4. Deploy

Railway will automatically:
- ✅ Build your React frontend
- ✅ Build your Python backend
- ✅ Serve everything from one URL
- ✅ Assign a domain (e.g., `https://hydra-production.up.railway.app`)
- ✅ Monitor health at `/api/health`

### 5. Set ALLOWED_ORIGINS

After deployment completes:

1. **Copy your Railway URL** from the dashboard (e.g., `hydra-production.up.railway.app`)
2. **Go to Variables** → Add new variable:
   ```bash
   ALLOWED_ORIGINS=https://hydra-production.up.railway.app
   ```
   Replace with your actual Railway URL (include `https://`)
3. Railway will auto-redeploy with the new variable

### 6. Configure Custom Domain (Optional)

To use `hydra.kurbanintelligence.lab`:

**In Railway Dashboard:**
1. Go to **Settings** → **Domains**
2. Click **Custom Domain**
3. Enter: `hydra.kurbanintelligence.lab`
4. Railway will show DNS records to configure

**Update DNS Records** (in your DNS provider for `kurbanintelligence.lab`):
```
Type: CNAME
Name: hydra
Value: <your-railway-app>.up.railway.app
TTL: Auto or 3600
```

*Alternative if CNAME not supported:*
```
Type: A
Name: hydra
Value: <IP provided by Railway>
```

**Set Environment Variable:**
```bash
ALLOWED_ORIGINS=https://hydra.kurbanintelligence.lab
```

**Wait for DNS propagation:**
- Usually takes 5-30 minutes
- Can take up to 48 hours in rare cases
- Railway will automatically provision SSL certificate
- Access your app at `https://hydra.kurbanintelligence.lab`

---

## Architecture Overview

### Production (Railway)
- **Single unified container** serves both frontend and backend
- **Frontend**: React/Vite app built to static files, served by FastAPI
- **Backend**: FastAPI handles `/api/*` routes
- **Routing**: All non-API routes serve the React SPA

### How it Works
1. Multi-stage Docker build:
   - Stage 1: Node.js builds the React frontend → `/app/frontend/dist`
   - Stage 2: Python serves API + static files
2. FastAPI routes:
   - `/api/*` → Backend API endpoints
   - `/*` → React frontend (SPA with fallback routing)

---

## Local Development

### Option 1: Separate Frontend/Backend (Recommended for dev)

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Access at: `http://localhost:5173` (Vite dev server proxies API to `:8000`)

### Option 2: Docker Compose (Production-like)

```bash
docker-compose up
```

Access at: `http://localhost:8000` (unified app)

To stop:
```bash
docker-compose down
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ Yes | - | Your OpenRouter API key |
| `ALLOWED_ORIGINS` | ✅ Yes | `localhost` | CORS allowed origins (use your custom domain) |
| `SESSION_SECRET_KEY` | ⚠️ Recommended | `dev-secret-key` | Secret for session signing (generate with `openssl rand -hex 32`) |
| `SESSION_MAX_AGE` | No | `7200` | Session duration in seconds (2 hours) |
| `OPENROUTER_MODEL` | No | `anthropic/claude-sonnet-4` | LLM model to use |
| `PORT` | No | `8000` | Port to run on (Railway sets this automatically) |

---

## Troubleshooting

### Build Fails
- Check Railway build logs for specific errors
- Ensure `frontend/package.json` is valid
- Ensure `backend/requirements.txt` has no typos

### Health Check Fails
- Verify app starts on Railway's `$PORT` variable
- Check if `OPENROUTER_API_KEY` is set
- View Railway logs for startup errors

### API Returns 500 Errors
- Check `OPENROUTER_API_KEY` is valid
- View Railway logs for Python exceptions
- Ensure OpenRouter account has credits

### Frontend Shows White Screen
- Check browser console for errors
- Verify static files built correctly (Railway build logs)
- Check CORS - ensure `ALLOWED_ORIGINS` includes your domain

### CORS Errors
- Update `ALLOWED_ORIGINS` in Railway variables
- Format: `https://hydra.kurbanintelligence.lab` (no trailing slash)
- Redeploy after changing environment variables
- Ensure domain matches exactly (including https://)

### Custom Domain Not Working
- Verify DNS records are correct (use `dig hydra.kurbanintelligence.lab`)
- Check DNS propagation: https://dnschecker.org
- Ensure SSL certificate is provisioned in Railway (automatic)
- Wait up to 48 hours for global DNS propagation

---

## Monitoring

### Health Check
Visit `/api/health` to verify the app is running:
```bash
curl https://hydra.kurbanintelligence.lab/api/health
```

Should return:
```json
{"status": "ok", "version": "1.0.0"}
```

### Railway Logs
View real-time logs in Railway dashboard under **Deployments** → **View Logs**

---

## Deployment Checklist

Before deploying to production:

- [ ] Generate secure `SESSION_SECRET_KEY` with `openssl rand -hex 32`
- [ ] Set `OPENROUTER_API_KEY` in Railway
- [ ] Configure custom domain in Railway
- [ ] Update DNS records for `hydra.kurbanintelligence.lab`
- [ ] Set `ALLOWED_ORIGINS=https://hydra.kurbanintelligence.lab`
- [ ] Test health endpoint after deployment
- [ ] Verify frontend loads correctly
- [ ] Test API endpoints work
- [ ] Check Railway logs for errors

---

## Cost Estimation

Railway pricing (as of 2024):
- **Hobby Plan**: $5/month for 500 hours execution time
- **Pro Plan**: $20/month for usage-based billing
- Typically costs $5-15/month for a small app like HyDRA

**Free tier available** with limited hours - good for testing!

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway Custom Domains**: https://docs.railway.app/deploy/exposing-your-app#custom-domains
- **Railway Status**: https://status.railway.app
- **OpenRouter Docs**: https://openrouter.ai/docs
