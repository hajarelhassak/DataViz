"""
JSONStorageService — gestion du stockage JSON local.

Utilisé pour le mode On-Premise.

Responsabilités :
- Sauvegarder des métadonnées JSON.
- Charger des configurations.
- Gérer les snapshots.

Sécurité :
- Aucun stockage de données brutes clientes.
- Aucun mot de passe ou credential.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path



class JSONStorageService:


    BASE_PATH = Path(
        "storage"
    )


    # =====================================================
    # Initialisation dossier stockage
    # =====================================================

    @staticmethod
    def _ensure_directory(
        folder: str
    ) -> Path:

        path = (
            JSONStorageService.BASE_PATH
            /
            folder
        )


        path.mkdir(
            parents=True,
            exist_ok=True
        )


        return path



    # =====================================================
    # Sauvegarde JSON
    # =====================================================

    @staticmethod
    def save_json(
        folder: str,
        filename: str,
        data: dict
    ) -> str:

        """
        Sauvegarde un dictionnaire JSON.

        Exemple :
        save_json(
            "schemas",
            "client_schema.json",
            schema
        )
        """


        directory = (
            JSONStorageService
            ._ensure_directory(folder)
        )


        file_path = (
            directory
            /
            filename
        )


        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:


            json.dump(

                data,

                file,

                ensure_ascii=False,

                indent=4

            )


        return str(
            file_path
        )



    # =====================================================
    # Lecture JSON
    # =====================================================

    @staticmethod
    def load_json(
        folder: str,
        filename: str
    ) -> dict | None:


        file_path = (

            JSONStorageService.BASE_PATH

            /

            folder

            /

            filename

        )


        if not file_path.exists():

            return None



        with open(

            file_path,

            "r",

            encoding="utf-8"

        ) as file:


            return json.load(
                file
            )



    # =====================================================
    # Suppression fichier
    # =====================================================

    @staticmethod
    def delete_json(
        folder: str,
        filename: str
    ) -> bool:


        file_path = (

            JSONStorageService.BASE_PATH

            /

            folder

            /

            filename

        )


        if file_path.exists():

            file_path.unlink()

            return True


        return False



    # =====================================================
    # Sauvegarde schéma BDD
    # =====================================================

    @staticmethod
    def save_schema(
        connection_id: str,
        schema: dict
    ) -> str:


        return JSONStorageService.save_json(

            "schemas",

            f"{connection_id}.json",

            schema

        )



    # =====================================================
    # Sauvegarde profil données
    # =====================================================

    @staticmethod
    def save_data_profile(
        connection_id: str,
        profile: dict
    ) -> str:


        return JSONStorageService.save_json(

            "profiles",

            f"{connection_id}.json",

            profile

        )



    # =====================================================
    # Sauvegarde recommandation IA
    # =====================================================

    @staticmethod
    def save_ai_recommendation(
        dashboard_id: str,
        recommendation: dict
    ) -> str:


        return JSONStorageService.save_json(

            "ai_reports",

            f"{dashboard_id}.json",

            recommendation

        )



    # =====================================================
    # Sauvegarde dashboard
    # =====================================================

    @staticmethod
    def save_dashboard_snapshot(
        dashboard_id: str,
        dashboard_data: dict
    ) -> str:


        snapshot = {

            "created_at":
                datetime.utcnow().isoformat(),


            "dashboard":
                dashboard_data

        }


        return JSONStorageService.save_json(

            "dashboards",

            f"{dashboard_id}.json",

            snapshot

        )