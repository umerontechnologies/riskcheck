# riskcheck
RiskCheck is an open-source full-stack risk analysis platform that evaluates public web signals to generate structured risk reports and safer transaction recommendations.
# RiskCheck (Full Stack)

This folder contains a working **frontend + backend** build for RiskCheck.

## Quick start (local)

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Create .env (copy backend/.env.example and fill your keys)
python -m uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:
- http://localhost:5173

## Google search keys

The backend uses **Google Programmable Search Engine (Custom Search JSON API)** to do public web footprint checks.

Put these in **backend/.env**:

```
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_CX=...
GOOGLE_CSE_GL=pk
```

> Notes:
> - The `<script async src="https://cse.google.com/cse.js?...` snippet is only for embedding a search widget on a website. This app uses the JSON API, so you **do not** paste that script.
> - For best results, your Programmable Search Engine should be configured to **Search the entire web**.

## Admin approvals

Community reports are stored as `pending` by default. To approve a report:

1. Set `ADMIN_TOKEN` in backend/.env
2. Call:

```
POST /api/admin/reports/{id}/approve
X-Admin-Token: <your token>
```

## Limitations (important)

- Some platforms (e.g., private Facebook groups) cannot be fully verified without official platform APIs and user permissions.
- RiskCheck never labels anyone as a scammer — it estimates risk/uncertainty and recommends safer transaction steps.

Contact Me For More Details
+92 312 9696 292
umerontechnologies@gmail.com
