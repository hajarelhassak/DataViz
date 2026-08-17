"""
UserRepository — accès aux utilisateurs.

Utilisé par AuthService pour :
- recherche email ;
- récupération utilisateur ;
- création/modification.
"""

from __future__ import annotations

from app.extensions import db

from models.user import User
from models.role import Role



class UserRepository:



    @staticmethod
    def get_by_id(
        user_id:str
    )->User | None:


        return User.query.get(user_id)



    @staticmethod
    def get_by_email(
        email:str
    )->User | None:


        return (

            User.query

            .filter_by(
                email=email.lower()
            )

            .first()
        )



    @staticmethod
    def create(
        nom:str,
        email:str,
        password_hash:str,
        role_id:str
    )->User:


        user = User(

            nom=nom,

            email=email.lower(),

            password_hash=password_hash,

            role_id=role_id
        )


        db.session.add(user)

        db.session.commit()


        return user



    @staticmethod
    def update(
        user:User,
        **kwargs
    )->User:


        allowed={

            "nom",

            "email",

            "is_active",

            "role_id"

        }


        for key,value in kwargs.items():

            if key in allowed:

                setattr(
                    user,
                    key,
                    value
                )


        db.session.commit()


        return user



    @staticmethod
    def delete(
        user:User
    )->None:


        db.session.delete(user)

        db.session.commit()



    @staticmethod
    def list_all()->list[User]:


        return (

            User.query

            .order_by(
                User.created_at.desc()
            )

            .all()
        )