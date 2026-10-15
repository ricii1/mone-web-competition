import hashlib
import time

from fastapi import HTTPException, Request

from app.realtime.pubsub import get_redis


async def limit_auth_requests(request: Request) -> None:
    """Bound expensive authentication work using the existing shared Redis."""
    registration = request.url.path.endswith("/register")
    window = 3600 if registration else 60
    limit = 20 if registration else 10
    bucket = int(time.time() // window)
    body = await request.json()
    email = str(body.get("email", "")).strip().casefold() if isinstance(body, dict) else ""
    address = request.client.host if request.client else "unknown"
    action = "register" if registration else "login"
    redis = get_redis()
    keys = [
        f"auth:{action}:{kind}:{hashlib.sha256(value.encode()).hexdigest()}:{bucket}"
        for kind, value in (("ip", address), ("email", email))
    ]
    async with redis.pipeline(transaction=True) as pipe:
        for key in keys:
            pipe.incr(key)
            pipe.expire(key, window * 2)
        counts = await pipe.execute()
    if any(count > limit for count in counts[::2]):
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak percobaan. Tunggu sebentar lalu coba lagi",
            headers={"Retry-After": str(max(1, window - int(time.time()) % window))},
        )
