"""
Modèle Role — gère les rôles utilisateurs.
"""
import uuid
from app.extensions import db
def _uuid():
    return str(uuid.uuid4())

class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    nom = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship("User", back_populates="role")

    ADMIN_SYSTEME = "admin_systeme"
    ADMIN_APPLICATION = "admin_application"
    UTILISATEUR_METIER = "utilisateur_metier"

    def __repr__(self):
        return f"<Role {self.nom}>"