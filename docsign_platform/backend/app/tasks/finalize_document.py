import os
import fitz  # PyMuPDF
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.crud import crud_envelope
from app.utils.helpers import calculate_sha256
from app.core.config import settings

@celery_app.task
def finalize_envelope_task(envelope_id: str):
    """
    Celery task to finalize a signed document.
    1. Generates an audit certificate PDF.
    2. Stamps all signatures and text fields onto the original PDF.
    3. Merges the stamped PDF and the certificate.
    4. Calculates the final hash and updates the envelope record.
    """
    db = SessionLocal()
    try:
        envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
        if not envelope:
            print(f"Error: Envelope {envelope_id} not found for finalization.")
            return

        # --- 1. Generate Audit Certificate ---
        cert_path = _create_audit_certificate(envelope)

        # --- 2. Stamp the original document ---
        stamped_path = _stamp_document(envelope)

        # --- 3. Merge Stamped Doc and Certificate ---
        final_doc_path = _merge_pdfs(stamped_path, cert_path, envelope.id)

        # --- 4. Calculate Final Hash & Update DB ---
        final_hash = calculate_sha256(final_doc_path)
        
        envelope.signed_doc_path = final_doc_path
        envelope.final_hash = final_hash
        db.commit()

        # --- 5. Cleanup temporary files ---
        os.remove(cert_path)
        os.remove(stamped_path)

        print(f"Successfully finalized envelope {envelope_id}. Final document at: {final_doc_path}")
        # TODO: Trigger email task to send the final document to all parties.

    finally:
        db.close()

def _create_audit_certificate(envelope) -> str:
    """Generates a PDF certificate with audit trail info."""
    path = os.path.join(settings.STORAGE_BASE_PATH, f"cert_{envelope.id}.pdf")
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    
    c.drawString(72, height - 72, "Certificate of Completion")
    c.drawString(72, height - 100, f"Envelope ID: {envelope.id}")
    c.drawString(72, height - 120, f"Status: {envelope.status}")
    c.drawString(72, height - 150, "Audit Trail:")
    
    y_pos = height - 170
    for log in envelope.audit_trails:
        log_time = log.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        log_entry = f"[{log_time}] - {log.event}"
        if log.ip_address:
            log_entry += f" (IP: {log.ip_address})"
        c.drawString(90, y_pos, log_entry)
        y_pos -= 20
        if y_pos < 50: # Handle page overflow if many logs
            c.showPage()
            y_pos = height - 72

    c.save()
    return path

def _stamp_document(envelope) -> str:
    """Stamps all fields onto a copy of the original PDF."""
    doc = fitz.open(envelope.original_doc_path)
    
    for field in envelope.fields:
        page = doc.load_page(field.page_number - 1)
        page_width, page_height = page.rect.width, page.rect.height
        
        # Convert percentage coordinates back to absolute PDF points
        x1 = field.x_coord * page_width / 100
        y1 = field.y_coord * page_height / 100
        x2 = (field.x_coord + field.width) * page_width / 100
        y2 = (field.y_coord + field.height) * page_height / 100
        rect = fitz.Rect(x1, y1, x2, y2)
        
        if field.type in ["signature", "initial"] and field.value:
            page.insert_image(rect, filename=field.value)
        elif field.type == "date" and field.value:
            # Simple date stamping
             page.insert_textbox(rect, f"Signed: {field.value}", fontsize=9, align=fitz.TEXT_ALIGN_CENTER)
        elif field.type == "text" and field.value:
            page.insert_textbox(rect, field.value, fontsize=9, align=fitz.TEXT_ALIGN_LEFT)
            
    stamped_path = os.path.join(settings.STORAGE_BASE_PATH, f"stamped_{envelope.id}.pdf")
    doc.save(stamped_path)
    doc.close()
    return stamped_path

def _merge_pdfs(stamped_path: str, cert_path: str, envelope_id: str) -> str:
    """Merges the stamped document with the certificate."""
    merger = PdfWriter()
    
    merger.append(stamped_path)
    merger.append(cert_path)
    
    signed_dir = os.path.join(settings.STORAGE_BASE_PATH, "signed")
    os.makedirs(signed_dir, exist_ok=True)
    final_path = os.path.join(signed_dir, f"signed_{envelope_id}.pdf")
    
    with open(final_path, "wb") as f:
        merger.write(f)
    merger.close()
    return final_path