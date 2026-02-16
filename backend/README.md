https://www.gnu.org/licenses/agpl-3.0.txt
This project is licensed under the GNU Affero General Public License v3.0.


# RiskCheck Backend (FastAPI)

## 1) Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in `backend/` (copy `.env.example`).

## 2) Run

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API will be available at:
- http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Notes
- Google search signals work only if `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_CX` are set.
- Community reports are stored in SQLite (`riskcheck.db`) and are **pending** until approved.
- Approve a report (optional admin):

```bash
curl -X POST "http://127.0.0.1:8000/api/admin/reports/1/approve" -H "X-Admin-Token: <your ADMIN_TOKEN>"
```
