import hashlib
import hmac

from fastapi import HTTPException, Request


async def verify_hmac_sha256(
    request: Request,
    secret: str,
    header: str = "x-hub-signature-256",
) -> None:
    body = await request.body()
    signature = request.headers.get(header, "")
    if not signature.startswith("sha256="):
        raise HTTPException(status_code=400, detail="Missing HMAC signature header")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")
