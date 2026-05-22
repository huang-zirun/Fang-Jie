import hashlib
import hmac
import base64
import random
import time
import uuid
from datetime import datetime, timezone

import httpx

from app.config import settings


_code_store: dict[str, tuple[str, float]] = {}


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _is_expired(expires_at: float) -> bool:
    return time.time() > expires_at


async def _send_aliyun_sms(phone: str, code: str) -> None:
    import json

    params = {
        "PhoneNumbers": phone,
        "SignName": settings.SMS_SIGN_NAME,
        "TemplateCode": settings.SMS_TEMPLATE_CODE,
        "TemplateParam": json.dumps({"code": code}),
        "Action": "SendSms",
        "Version": "2017-05-25",
        "Format": "JSON",
        "AccessKeyId": settings.SMS_ACCESS_KEY,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
        "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    sorted_params = sorted(params.items())
    query_string = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted_params
    )
    string_to_sign = f"GET&{_percent_encode('/')}&{_percent_encode(query_string)}"
    signature = _hmac_sha1(settings.SMS_SECRET_KEY + "&", string_to_sign)
    params["Signature"] = signature

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://dysmsapi.aliyuncs.com/", params=params)
        data = resp.json()
        if data.get("Code") != "OK":
            raise RuntimeError(f"SMS send failed: {data.get('Message', 'Unknown error')}")


def _percent_encode(s: str) -> str:
    import urllib.parse

    return urllib.parse.quote(s, safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _hmac_sha1(key: str, msg: str) -> str:
    hashed = hmac.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(hashed.digest()).decode("utf-8")


async def send_verification_code(phone: str) -> None:
    if settings.SMS_ENABLED:
        code = _generate_code()
        if settings.SMS_GATEWAY == "aliyun":
            await _send_aliyun_sms(phone, code)
        else:
            raise RuntimeError(f"Unsupported SMS gateway: {settings.SMS_GATEWAY}")
    else:
        code = "123456"

    _code_store[phone] = (code, time.time() + 300)


def verify_code(phone: str, code: str) -> bool:
    entry = _code_store.get(phone)
    if entry is None:
        return False
    stored_code, expires_at = entry
    if _is_expired(expires_at):
        del _code_store[phone]
        return False
    if stored_code != code:
        return False
    del _code_store[phone]
    return True
