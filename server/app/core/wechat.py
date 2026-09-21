import httpx

from app.core.exceptions import AppError, ErrorCode
from app.core.settings import get_settings


CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def _wechat_login_failed() -> AppError:
    return AppError(
        ErrorCode.WECHAT_LOGIN_FAILED,
        "Unable to complete WeChat login",
        502,
    )


async def _request_openid(client: httpx.AsyncClient, code: str) -> str:
    settings = get_settings()
    try:
        response = await client.get(
            CODE2SESSION_URL,
            params={
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        payload: object = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise _wechat_login_failed() from exc

    if not isinstance(payload, dict) or payload.get("errcode"):
        raise _wechat_login_failed()

    openid = payload.get("openid")
    if not isinstance(openid, str) or not openid:
        raise _wechat_login_failed()
    return openid


async def exchange_code_for_openid(
    code: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    normalized_code = code.strip()
    if not normalized_code:
        raise AppError(ErrorCode.VALIDATION, "WeChat code is required", 400)

    settings = get_settings()
    if settings.is_local_fake_wechat():
        return f"local:{normalized_code}"
    if not settings.wechat_secret:
        raise _wechat_login_failed()

    if client is not None:
        return await _request_openid(client, normalized_code)

    async with httpx.AsyncClient(timeout=10.0) as owned_client:
        return await _request_openid(owned_client, normalized_code)
