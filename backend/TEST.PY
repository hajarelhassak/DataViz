import sys
from pathlib import Path

# ==========================================================
# CHEMIN BACKEND
# ==========================================================

BACKEND_DIR = Path(__file__).resolve().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ==========================================================
# IMPORTS
# ==========================================================

from app import create_app
from app.extensions import db

from models.user import User
from models.role import Role


# ==========================================================
# APPLICATION
# ==========================================================

app = create_app()


# ==========================================================
# CREATION ADMIN
# ==========================================================

with app.app_context():

    print("======================================")
    print("INITIALISATION UTILISATEUR ADMIN")
    print("======================================")

    # ------------------------------------------------------
    # 1. CHERCHER LE ROLE ADMIN
    # ------------------------------------------------------

    role = Role.query.filter_by(
        nom="admin"
    ).first()

    # ------------------------------------------------------
    # 2. CREER LE ROLE S'IL N'EXISTE PAS
    # ------------------------------------------------------

    if role is None:

        print("Role admin introuvable.")
        print("Création du rôle admin...")

        role = Role(
            nom="admin",
            description="Administrateur de DataViz"
        )

        db.session.add(role)
        db.session.commit()

        print("Role admin créé.")

    else:

        print("Role admin déjà existant.")

    # ------------------------------------------------------
    # 3. CHERCHER L'UTILISATEUR
    # ------------------------------------------------------

    email = "admin@test.local"

    user = User.query.filter_by(
        email=email
    ).first()

    # ------------------------------------------------------
    # 4. CREER OU REINITIALISER L'ADMIN
    # ------------------------------------------------------

    if user is None:

        print("Utilisateur admin introuvable.")
        print("Création de l'utilisateur...")

        user = User(
            nom="Admin",
            email=email,
            role_id=role.id,
            is_active=True
        )

        user.set_password("admin123")

        db.session.add(user)
        db.session.commit()

        print("Utilisateur admin créé.")

    else:

        print("Utilisateur admin déjà existant.")

        # On rattache l'utilisateur au rôle admin
        user.role_id = role.id

        # On s'assure qu'il est actif
        user.is_active = True

        # On réinitialise temporairement le mot de passe
        user.set_password("admin123")

        db.session.commit()

        print("Utilisateur admin mis à jour.")

    # ------------------------------------------------------
    # 5. AFFICHAGE
    # ------------------------------------------------------

    print()
    print("======================================")
    print("INITIALISATION TERMINEE")
    print("======================================")
    print(f"Nom          : {user.nom}")
    print(f"Email        : {user.email}")
    print(f"Role         : {role.nom}")
    print(f"Actif        : {user.is_active}")
    print("Mot de passe : admin123")
    print("======================================")