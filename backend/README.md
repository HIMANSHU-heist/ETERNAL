# Step 1 — Universal file upload + schema detection backend

## Kaay banla ahe ithe
- FastAPI backend
- `/api/v1/upload` — CSV, TSV, Excel (.xlsx/.xls), JSON, Parquet upload karta yeto
- Prattyek upload zalyavar auto schema detect hoto: column types, missing values, unique counts, min/max/mean for numeric columns, sample values for text columns
- `/api/v1/dataset/{id}/preview` — pahilya N rows baghayla

## Kasa run karaych (local machine var)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Server chalu zalyavar browser madhe ja: **http://localhost:8000/docs**
Ithe Swagger UI dista — tithun directly file upload test karu shakto, curl kinva Postman lagat nahi.

## Kasa test karaych (curl ne)

```bash
# Health check
curl http://localhost:8000/

# File upload (CSV/Excel/JSON konतahi)
curl -X POST http://localhost:8000/api/v1/upload -F "file=@/path/to/your/data.csv"

# Preview (upload response madhun dataset_id ghe)
curl http://localhost:8000/api/v1/dataset/<dataset_id>/preview?rows=5
```

## Ithe already tested ahe (mi swतः kelay)
- Server start ✅
- CSV upload with missing values ✅ (age, salary madhe null values hote — barobar detect zale)
- Schema summary (dtypes, min/max/mean, sample values) ✅
- Preview endpoint ✅

## Pudhcha step (Step 2)
- Chat endpoint: LLM ला schema summary pathvun natural language questions cha answer
- Database (SQLite) — in-memory registry cha jaagi
- Frontend (Streamlit/React) jya madhe upload + chat UI asel
