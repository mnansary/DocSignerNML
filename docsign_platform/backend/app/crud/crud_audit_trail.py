from sqlalchemy.orm import Session
from app.models.audit_trail import AuditTrail

def create_audit_log(
    db: Session,
    *,
    envelope_id: str,
    event: str,
    ip_address: str | None = None
) -> AuditTrail:
    """
    Creates a new audit trail log entry.
    """
    db_log = AuditTrail(
        envelope_id=envelope_id,
        event=event,
        ip_address=ip_address
    )
    db.add(db_log)
    # The commit will happen as part of the larger transaction in the API layer
    return db_log