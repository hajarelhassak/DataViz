"""
Tests du chiffrement des credentials de connexion (Partie 5 Q12 / Partie 9
du guide). C'est une des parties les plus critiques du projet en matière
de sécurité — elle mérite des tests dédiés (Partie 14 : "priorise les
tests sur les parties à risque").
"""
import pytest

from utils.crypto import DecryptionError, decrypt_value, encrypt_value


def test_encrypt_then_decrypt_returns_original_value(app):
    original = "MotDePasseSuperSecret!123"
    with app.app_context():
        ciphertext = encrypt_value(original)
        assert ciphertext != original  # jamais stocké en clair
        decrypted = decrypt_value(ciphertext)
    assert decrypted == original


def test_ciphertext_is_not_reversible_without_correct_key(app):
    with app.app_context():
        ciphertext = encrypt_value("secret")
        with pytest.raises(DecryptionError):
            # simule une tentative de déchiffrement avec un ciphertext corrompu
            decrypt_value(ciphertext[:-2] + "xx")