# PDF Report Generator

A small FastAPI service that turns SQL aggregation into a background-generated PDF artifact.

## Pipeline

1. `POST /sales` stores sample sales data in SQLite.
2. `POST /reports` creates a queued report job and returns immediately with a job ID.
3. The background task aggregates sales by product with SQL.
4. ReportLab renders the aggregation into `artifacts/report-{id}.pdf`.
5. `GET /reports/{id}` exposes job status and a download URL.
6. `GET /reports/{id}/download` streams the stored PDF artifact instead of passing the PDF through the job response.

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open Swagger at `http://127.0.0.1:8000/docs`.

## Example

```bash
curl -X POST "http://127.0.0.1:8000/sales?product=Keyboard&amount=1200"
curl -X POST "http://127.0.0.1:8000/sales?product=Mouse&amount=600"
curl -X POST "http://127.0.0.1:8000/reports"
curl "http://127.0.0.1:8000/reports/1"
curl -o report.pdf "http://127.0.0.1:8000/reports/1/download"
```

## Stretch goal

The current implementation supports on-demand generation. A scheduler can call the same report-job creation path on a daily/weekly cadence without changing the report generation logic.
