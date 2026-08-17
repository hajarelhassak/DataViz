"""
Gestion du chiffrement des credentials BDD clientes.

Les mots de passe utilisateurs :
bcrypt → hash irréversible.

Les mots de passe des connexions externes :
Fernet → chiffrement réversible.

La clé est stockée uniquement dans les variables d'environnement.
"""


from cryptography.fernet import Fernet, InvalidToken
from flask import current_app



class DecryptionError(Exception):
    pass




def _get_fernet():

    key = current_app.config.get(
        "ENCRYPTION_KEY"
    )


    if not key:

        raise RuntimeError(
            "ENCRYPTION_KEY absente."
        )


    if isinstance(key, str):

        key = key.encode()


    return Fernet(key)




def encrypt_value(
    plain_text: str
) -> str:


    if not plain_text:

        raise ValueError(
            "Impossible de chiffrer une valeur vide."
        )


    return (
        _get_fernet()
        .encrypt(
            plain_text.encode()
        )
        .decode()
    )




def decrypt_value(
    ciphertext: str
) -> str:


    try:

        return (
            _get_fernet()
            .decrypt(
                ciphertext.encode()
            )
            .decode()
        )


    except InvalidToken as exc:

        raise DecryptionError(
            "Impossible de déchiffrer la donnée."
        ) from exc




def generate_new_key():

    return Fernet.generate_key().decode()