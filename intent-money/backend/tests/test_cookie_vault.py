import pytest
from cryptography.exceptions import InvalidTag

from app.services.cookie_vault import CookieVault


@pytest.fixture
def vault():
    return CookieVault()


def test_encrypt_decrypt_roundtrip(vault):
    original = "sessionid=abc123; token=xyz789"
    user_id = "test-user-001"
    ciphertext, iv = vault.encrypt(original, user_id)
    decrypted = vault.decrypt(ciphertext, iv, user_id)
    assert decrypted == original


def test_encrypt_produces_different_ciphertexts(vault):
    original = "sessionid=abc123"
    user_id = "test-user-001"
    ct1, iv1 = vault.encrypt(original, user_id)
    ct2, iv2 = vault.encrypt(original, user_id)
    assert ct1 != ct2 or iv1 != iv2


def test_decrypt_with_wrong_user_id_fails(vault):
    original = "sessionid=abc123"
    ct, iv = vault.encrypt(original, "user-a")
    with pytest.raises(InvalidTag):
        vault.decrypt(ct, iv, "user-b")


def test_encrypt_dict_input(vault):
    data = {"sessionid": "abc123", "token": "xyz"}
    user_id = "test-user-001"
    ct, iv = vault.encrypt(data, user_id)
    result = vault.decrypt(ct, iv, user_id)
    assert "sessionid" in result
    assert "abc123" in result


def test_tampered_ciphertext_fails(vault):
    original = "sessionid=abc123"
    user_id = "test-user-001"
    ct, iv = vault.encrypt(original, user_id)
    tampered_ct = ct[:-4] + "XXXX"
    with pytest.raises(InvalidTag):
        vault.decrypt(tampered_ct, iv, user_id)
