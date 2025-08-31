from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.models.audit_log import AuditLogCreate


def create_audit_log(db: Session, *, obj_in: AuditLogCreate) -> AuditLog:
    """
    Creates a new audit log entry.
    """
    db_obj = AuditLog(
        document_id=obj_in.document_id,
        user_id=obj_in.user_id,
        action=obj_in.action,
        details=obj_in.details,
        ip_address=obj_in.ip_address,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
