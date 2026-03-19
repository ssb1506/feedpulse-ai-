# Deployment Guide — GCP Cloud Run + GitHub Actions + Upstash Kafka

Total cost: **$0** (all free tiers)

---

## What goes where

| Component | Platform | Free tier |
|-----------|----------|-----------|
| Frontend (React) | GCP Cloud Run | 2M requests/month free |
| Backend (FastAPI + AI) | GCP Cloud Run | 2M requests/month free |
| Kafka streaming | Upstash Kafka | 10K messages/day free |
| LLM (Gemini) | Google AI Studio | 15 RPM free |
| Code + CI/CD | GitHub + Actions | Free for public repos |

---

## Step 1: Set up Upstash Kafka (5 minutes)

1. Go to [console.upstash.com](https://console.upstash.com)
2. Sign up with GitHub (no credit card needed)
3. Click **Create Cluster**
   - Name: `feedpulse`
   - Region: `us-east-1` (closest to GCP us-central1)
   - Type: Single zone (free)
4. Click **Topics** → **Create Topic**
   - Name: `social-posts`
   - Partitions: 1
5. Go to cluster **Details** tab and copy:
   - **Endpoint** → this is your `KAFKA_BOOTSTRAP_SERVERS`
   - **Username** → this is your `KAFKA_USERNAME`
   - **Password** → this is your `KAFKA_PASSWORD`

Save these — you'll need them in Step 3.

---

## Step 2: Get a Gemini API key (2 minutes)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Copy the key — this is your `GEMINI_API_KEY`

---

## Step 3: Set up GCP project (10 minutes)

### 3a. Create project
```bash
# Install gcloud CLI if you haven't: https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud projects create feedpulse-ai --name="FeedPulse AI"
gcloud config set project feedpulse-ai

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3b. Create a service account for GitHub Actions
```bash
# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding feedpulse-ai \
  --member="serviceAccount:github-deployer@feedpulse-ai.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding feedpulse-ai \
  --member="serviceAccount:github-deployer@feedpulse-ai.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding feedpulse-ai \
  --member="serviceAccount:github-deployer@feedpulse-ai.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Download the key (save this JSON file)
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=github-deployer@feedpulse-ai.iam.gserviceaccount.com
```

---

## Step 4: Push to GitHub (5 minutes)

```bash
cd feedpulse-ai

git init
git add .
git commit -m "Initial commit - FeedPulse AI"

# Create repo on GitHub (or use gh cli)
gh repo create feedpulse-ai --public --push
```

### Add GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 5 secrets:

| Secret name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | `feedpulse-ai` |
| `GCP_SA_KEY` | Contents of `gcp-key.json` (paste the entire JSON) |
| `GEMINI_API_KEY` | Your Gemini API key from Step 2 |
| `KAFKA_BOOTSTRAP_SERVERS` | Upstash endpoint from Step 1 |
| `KAFKA_USERNAME` | Upstash username from Step 1 |
| `KAFKA_PASSWORD` | Upstash password from Step 1 |

---

## Step 5: Deploy (automatic)

Push to main and GitHub Actions does the rest:

```bash
git push origin main
```

Go to your repo → **Actions** tab → watch the deployment.

When it's done, you'll get two URLs:
- `https://feedpulse-frontend-xxxxx-uc.a.run.app` → the dashboard
- `https://feedpulse-backend-xxxxx-uc.a.run.app` → the API

---

## Step 6: Verify it works

1. Open the frontend URL → you should see the dashboard
2. Wait 10-20 seconds → posts should start appearing in the live feed
3. Click **AI Assistant** → ask "What's trending?"
4. Check the API docs: `https://feedpulse-backend-xxxxx-uc.a.run.app/docs`

---

## Quick deploy without GitHub Actions (manual)

If you just want to deploy once without CI/CD:

```bash
# Backend
cd backend
gcloud run deploy feedpulse-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars "GEMINI_API_KEY=your-key" \
  --set-env-vars "KAFKA_BOOTSTRAP_SERVERS=your-upstash-endpoint" \
  --set-env-vars "KAFKA_USERNAME=your-username" \
  --set-env-vars "KAFKA_PASSWORD=your-password"

# Get the backend URL
BACKEND_URL=$(gcloud run services describe feedpulse-backend --region us-central1 --format 'value(status.url)')

# Frontend
cd ../frontend
# Update .env with backend URL
echo "VITE_API_URL=$BACKEND_URL" > .env
npm install && npm run build

gcloud run deploy feedpulse-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi
```

---

## Troubleshooting

**Posts not showing up?**
- Check Upstash console → Topics → `social-posts` → Messages tab
- If messages are there but not on dashboard, check backend logs: `gcloud run logs read feedpulse-backend`

**AI agent not responding?**
- Verify GEMINI_API_KEY is set: the agent works in fallback mode without it (shows data but no natural language)

**WebSocket disconnecting?**
- Cloud Run has a 60-minute timeout for WebSocket connections. The frontend auto-reconnects every 3 seconds.

**Container failing to start?**
- Backend needs 2Gi memory (ML models are large). Check: `gcloud run deploy ... --memory 2Gi`
