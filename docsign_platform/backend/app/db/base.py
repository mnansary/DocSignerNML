# Import all the models, so that Base has them registered automatically
# This is crucial for Alembic's autogenerate and for resolving relationships.
from app.db.base_class import Base # We will create this new file next
from app.models.envelope import Envelope
from app.models.recipient import Recipient
from app.models.field import Field
from app.models.audit_trail import AuditTrail