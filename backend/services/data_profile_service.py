"""
DataProfileService

Analyse la structure d'un DataFrame complet sans envoyer les données
brutes à l'IA.

Produit :
- nombre de lignes
- colonnes
- types
- valeurs nulles
- cardinalité
- statistiques simples

Utilisé avant l'appel IA.
"""

from __future__ import annotations

import pandas as pd


class DataProfileService:

    @staticmethod
    def generate_profile(df: pd.DataFrame) -> dict:
        """
        Génère un profil global du dataset.
        """

        profile = {
            "nombre_lignes": int(len(df)),
            "nombre_colonnes": int(len(df.columns)),
            "colonnes": []
        }


        for column in df.columns:

            serie = df[column]

            info = {

                "nom": column,

                "type_python": str(
                    serie.dtype
                ),

                "valeurs_nulles": int(
                    serie.isna().sum()
                ),

                "pourcentage_null": round(
                    float(serie.isna().mean() * 100),
                    2
                ),

                "valeurs_uniques": int(
                    serie.nunique()
                )

            }


            if pd.api.types.is_numeric_dtype(serie):

                info["statistiques"] = {

                    "min": float(serie.min()),

                    "max": float(serie.max()),

                    "moyenne": float(serie.mean()),

                    "ecart_type": float(
                        serie.std() or 0
                    )

                }


            elif pd.api.types.is_datetime64_any_dtype(serie):

                info["periode"] = {

                    "debut": str(
                        serie.min()
                    ),

                    "fin": str(
                        serie.max()
                    )

                }


            else:

                top = (
                    serie
                    .value_counts()
                    .head(5)
                    .to_dict()
                )

                info["valeurs_principales"] = {
                    str(k): int(v)
                    for k, v in top.items()
                }


            profile["colonnes"].append(info)


        return profile