import base64
import json
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

logger = logging.getLogger(__name__)

_DEV_KEY = base64.b64encode(b"dev-only-key--32-bytes-pad!!1234").decode()


class CookieVault:
    def __init__(self):
        key_b64 = settings.COOKIE_ENCRYPTION_KEY
        if not key_b64:
            if settings.ENV == "production":
                raise RuntimeError("COOKIE_ENCRYPTION_KEY must be set in production")
            logger.warning("Cookie加密密钥未配置，使用开发密钥(禁止用于生产)")
            key_b64 = _DEV_KEY
        self._key = base64.b64decode(key_b64)

    def encrypt(self, cookie_data: str | dict, user_id: str) -> tuple[str, str]:
        if isinstance(cookie_data, dict):
            cookie_data = json.dumps(cookie_data, ensure_ascii=False)
        iv = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(
            iv,
            cookie_data.encode("utf-8"),
            associated_data=user_id.encode("utf-8"),
        )
        return (
            base64.b64encode(ciphertext).decode("ascii"),
            base64.b64encode(iv).decode("ascii"),
        )

    def decrypt(self, ciphertext_b64: str, iv_b64: str, user_id: str) -> str:
        ciphertext = base64.b64decode(ciphertext_b64)
        iv = base64.b64decode(iv_b64)
        aesgcm = AESGCM(self._key)
        plaintext = aesgcm.decrypt(
            iv,
            ciphertext,
            associated_data=user_id.encode("utf-8"),
        )
        return plaintext.decode("utf-8")


cookie_vault = CookieVault()
