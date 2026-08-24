from pathlib import Path
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import ReportJob, Sale
from .report_service import generate_report

Base.metadata.create_all(bind=engine)
app = FastAPI(title="PDF Report Generator", version="1.0.0")

@app.post("/sales", status_code=201)
def create_sale(product: str, amount: int, db: Session = Depends(get_db)):
    if not product.strip() or amount < 0:
        raise HTTPException(400, "product must be non-empty and amount must be >= 0")
    sale = Sale(product=product.strip(), amount=amount)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale

@app.post("/reports", status_code=202)
def create_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = ReportJob(status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_job, job.id)
    return {"job_id": job.id, "status": job.status}

def _run_job(job_id: int):
    db = next(get_db())
    try:
        generate_report(job_id, db)
    finally:
        db.close()

@app.get("/reports/{job_id}")
def get_report(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ReportJob, job_id)
    if not job:
        raise HTTPException(404, "report job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "download_url": f"/reports/{job.id}/download" if job.status == "completed" else None,
        "error": job.error,
    }

@app.get("/reports/{job_id}/download")
def download_report(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ReportJob, job_id)
    if not job or job.status != "completed" or not job.file_path:
        raise HTTPException(404, "report is not ready")
    path = Path(job.file_path)
    if not path.exists():
        raise HTTPException(404, "report artifact not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)

@app.get("/health")
def health():
    return {"status": "ok"}
