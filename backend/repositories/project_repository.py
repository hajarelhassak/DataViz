"""
ProjectRepository — accès aux projets utilisateurs.
"""

from __future__ import annotations

from app.extensions import db

from models.project import Project



class ProjectRepository:



    @staticmethod
    def get_by_id(
        project_id:str
    )->Project | None:


        return Project.query.get(project_id)



    @staticmethod
    def get_by_owner_and_id(
        owner_id:str,
        project_id:str
    )->Project | None:


        return (
            Project.query
            .filter_by(
                id=project_id,
                owner_id=owner_id
            )
            .first()
        )



    @staticmethod
    def list_for_owner(
        owner_id:str
    )->list[Project]:


        return (

            Project.query

            .filter_by(owner_id=owner_id)

            .order_by(
                Project.created_at.desc()
            )

            .all()
        )



    @staticmethod
    def create(
        nom:str,
        owner_id:str,
        entreprise:str|None=None
    )->Project:


        project = Project(

            nom=nom,

            owner_id=owner_id,

            entreprise=entreprise
        )


        db.session.add(project)

        db.session.commit()


        return project



    @staticmethod
    def update(
        project:Project,
        **kwargs
    )->Project:


        allowed = {

            "nom",

            "entreprise"

        }


        for key,value in kwargs.items():

            if key in allowed:

                setattr(
                    project,
                    key,
                    value
                )


        db.session.commit()


        return project



    @staticmethod
    def delete(
        project:Project
    )->None:


        db.session.delete(project)

        db.session.commit()