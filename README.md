# PantryChef AI

An AI web app that turns whatever ingredients you have on hand into real,
cookable recipes — streamed live from Claude.

## Tech stack
- **Frontend:** single-page HTML/CSS/JS (no build step needed)
- **Backend:** Python FastAPI, streams Claude's response via Server-Sent Events
- **LLM:** Anthropic Claude API (`claude-haiku-4-5-20251001` by default)
- **Containerization:** Docker
- **Deployment:** AWS App Runner (free-tier friendly)

## Project structure
```
pantrychef/
├── app/
│   ├── main.py          # FastAPI backend
│   └── static/
│       └── index.html   # Frontend (served by FastAPI)
├── Dockerfile
├── requirements.txt
├── .env.example
└── .gitignore
```

## 1. Run locally

```bash
cd pantrychef
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your real ANTHROPIC_API_KEY

export $(cat .env | xargs)      # or use python-dotenv if you prefer
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000`.

## 2. Run with Docker

```bash
docker build -t pantrychef-ai .
docker run -p 8000:8000 --env-file .env pantrychef-ai
```

Visit `http://localhost:8000`.

## 3. Deploy to AWS (App Runner)

**Push the image to Amazon ECR:**
```bash
aws ecr create-repository --repository-name pantrychef-ai

aws ecr get-login-password --region <your-region> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.<your-region>.amazonaws.com

docker tag pantrychef-ai:latest <account-id>.dkr.ecr.<your-region>.amazonaws.com/pantrychef-ai:latest
docker push <account-id>.dkr.ecr.<your-region>.amazonaws.com/pantrychef-ai:latest
```

**Create the App Runner service:**
1. Open the AWS App Runner console → **Create service**.
2. Source: **Container registry** → **Amazon ECR** → select the `pantrychef-ai` image.
3. Deployment settings: manual or automatic (your choice).
4. Service settings:
   - Port: `8000`
   - Environment variables: add `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` here (never in the image or in git).
5. Instance size: smallest available (0.25 vCPU / 0.5 GB is enough for this app — keeps it free-tier friendly).
6. Create & deploy. App Runner gives you a public HTTPS URL when it's done.

**Cost control:** set an AWS Budget alert (Billing → Budgets → Create budget) at a low
threshold (e.g. $1) so you get an email if anything runs beyond free tier.

## Security notes
- The Anthropic API key lives only in the backend environment — it is never
  sent to or embedded in the frontend.
- `.env` is git-ignored; only `.env.example` (no real values) is committed.
- CORS is open here for demo simplicity; for a real production app, restrict
  `allow_origins` to your actual frontend domain.

## Sample prompts used during development
- "Scaffold a FastAPI endpoint that streams Anthropic Claude responses to the
  browser using Server-Sent Events."
- "Design a distinctive single-page frontend for a recipe generator — avoid
  generic AI-app look, lean into a kitchen/chalkboard visual theme."
- "Write a Dockerfile for a FastAPI app that also serves a static frontend
  from the same container."
