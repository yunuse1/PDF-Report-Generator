from datetime import datetime
from pathlib import Path
from sqlalchemy import func, select
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import ReportJob, Sale

REPORT_DIR = Path("artifacts")
REPORT_DIR.mkdir(exist_ok=True)

def generate_report(job_id: int, db):
    job = db.get(ReportJob, job_id)
    if not job:
        return
    job.status = "running"
    db.commit()
    try:
        rows = db.execute(
            select(Sale.product, func.count(Sale.id), func.sum(Sale.amount))
            .group_by(Sale.product)
            .order_by(func.sum(Sale.amount).desc())
        ).all()
        total = db.scalar(select(func.sum(Sale.amount)).select_from(Sale)) or 0
        path = REPORT_DIR / f"report-{job_id}.pdf"
        pdf = canvas.Canvas(str(path), pagesize=A4)
        pdf.setTitle(f"Sales Report #{job_id}")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(50, 800, "Sales Report")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 782, f"Generated: {datetime.utcnow():%Y-%m-%d %H:%M UTC}")
        pdf.drawString(50, 765, f"Total sales: {total}")
        y = 725
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, "Product")
        pdf.drawString(260, y, "Orders")
        pdf.drawString(350, y, "Revenue")
        pdf.setFont("Helvetica", 10)
        for product, count, revenue in rows:
            y -= 22
            if y < 60:
                pdf.showPage()
                y = 800
            pdf.drawString(50, y, str(product)[:30])
            pdf.drawString(260, y, str(count))
            pdf.drawString(350, y, str(revenue or 0))
        pdf.save()
        job.file_path = str(path)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        db.commit()
        raise
