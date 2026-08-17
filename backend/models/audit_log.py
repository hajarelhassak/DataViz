"""
Modèle AuditLog.

Stocke la traçabilité :
- connexion utilisateur ;
- test BDD ;
- appel IA ;
- export ;
- modifications sensibles.

Les données sensibles sont filtrées par AuditService.
"""

import uuid
import json

from datetime import datetime, timezone

from app.extensions import db



def _uuid():
    return str(uuid.uuid4())



class AuditLog(db.Model):

    __tablename__ = "audit_logs"



    __table_args__ = (

        db.Index(
            "idx_audit_user",
            "user_id"
        ),

        db.Index(
            "idx_audit_action",
            "action"
        ),

        db.Index(
            "idx_audit_created",
            "created_at"
        ),

    )



    id = db.Column(

        db.String(36),

        primary_key=True,

        default=_uuid
    )



    user_id = db.Column(

        db.String(36),

        db.ForeignKey("users.id"),

        nullable=True
    )



    action = db.Column(

        db.String(100),

        nullable=False
    )



    details_json = db.Column(

        db.Text,

        nullable=True
    )



    ip_address = db.Column(

        db.String(45),

        nullable=True
    )



    created_at = db.Column(

        db.DateTime,

        default=lambda:
            datetime.now(timezone.utc)
    )



    # relation

    user = db.relationship(

        "User",

        back_populates="audit_logs"

    )



    def to_dict(self):

        try:

            details = (
                json.loads(self.details_json)
                if self.details_json
                else None
            )

        except Exception:

            details = None



        return {

            "id":self.id,

            "user_id":self.user_id,

            "action":self.action,

            "details":details,

            "ip_address":self.ip_address,

            "created_at":
                self.created_at.isoformat()
                if self.created_at else None

        }



    def __repr__(self):

        return f"<AuditLog {self.action}>"