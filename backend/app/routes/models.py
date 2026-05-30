"""模型提供商管理 API（需认证 + SSRF 防护）。"""

import ipaddress
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException

from ..ai import llm_client
from ..routes.auth import get_current_user
from .. import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["models"])

PRESETS = [
    {"name": "DeepSeek Chat (V3)", "provider_type": "deepseek",
     "base_url": "https://api.deepseek.com/v1", "model_name": "deepseek-chat"},
    {"name": "DeepSeek Reasoner (R1)", "provider_type": "deepseek",
     "base_url": "https://api.deepseek.com/v1", "model_name": "deepseek-reasoner"},
    {"name": "OpenAI GPT-4.1", "provider_type": "openai",
     "base_url": "https://api.openai.com/v1", "model_name": "gpt-4.1"},
    {"name": "OpenAI GPT-4.1 mini", "provider_type": "openai",
     "base_url": "https://api.openai.com/v1", "model_name": "gpt-4.1-mini"},
    {"name": "OpenAI o4-mini", "provider_type": "openai",
     "base_url": "https://api.openai.com/v1", "model_name": "o4-mini"},
    {"name": "通义千问 qwen-max", "provider_type": "qwen",
     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen-max"},
    {"name": "通义千问 qwen-plus", "provider_type": "qwen",
     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen-plus"},
    {"name": "通义千问 Qwen3-235B", "provider_type": "qwen",
     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen3-235b-a22b"},
    {"name": "MiMo-7B (小米)", "provider_type": "mimo",
     "base_url": "https://api.xiaoai.mi.com/v1", "model_name": "mimo-7b-rl"},
    {"name": "自定义 (OpenAI 兼容)", "provider_type": "custom",
     "base_url": "", "model_name": ""},
]


def _validate_url(url: str) -> str:
    """验证 URL 安全性，防止 SSRF。"""
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")

    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise HTTPException(status_code=400, detail="仅支持 http/https 协议")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="无效的 URL")

    # 阻止访问内部网络
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise HTTPException(status_code=400, detail="不允许访问内部网络地址")
    except ValueError:
        # hostname 是域名，不是 IP — 检查是否是 localhost
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            raise HTTPException(status_code=400, detail="不允许访问 localhost")

    return url


@router.get("/presets")
def get_presets() -> dict:
    return {"presets": PRESETS}


@router.get("")
def list_providers(user: dict = Depends(get_current_user)) -> dict:
    return {"providers": storage.list_providers()}


@router.post("")
def create_provider(body: dict, user: dict = Depends(get_current_user)) -> dict:
    required = ["name", "provider_type", "base_url", "api_key", "model_name"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    _validate_url(body["base_url"])

    if body.get("is_default") or not storage.list_providers():
        body["is_default"] = True

    provider = storage.create_provider(body)
    llm_client.clear_cache()
    return {"provider": provider}


@router.put("/{provider_id}")
def update_provider(provider_id: int, body: dict,
                    user: dict = Depends(get_current_user)) -> dict:
    if body.get("base_url"):
        _validate_url(body["base_url"])
    provider = storage.update_provider(provider_id, body)
    if not provider:
        raise HTTPException(status_code=404, detail="提供商不存在")
    llm_client.clear_cache()
    return {"provider": provider}


@router.delete("/{provider_id}")
def delete_provider(provider_id: int, user: dict = Depends(get_current_user)) -> dict:
    if not storage.delete_provider(provider_id):
        raise HTTPException(status_code=404, detail="提供商不存在")
    llm_client.clear_cache()
    return {"status": "deleted"}


@router.post("/{provider_id}/test")
def test_provider(provider_id: int, user: dict = Depends(get_current_user)) -> dict:
    provider = storage.get_provider_raw(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="提供商不存在")
    result = llm_client.test_provider(provider_id)
    return result


@router.post("/{provider_id}/default")
def set_default(provider_id: int, user: dict = Depends(get_current_user)) -> dict:
    provider = storage.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="提供商不存在")
    storage.set_default_provider(provider_id)
    llm_client.clear_cache()
    return {"status": "ok", "default_id": provider_id}


def _fetch_models_from_api(base_url: str, api_key: str) -> list:
    """从提供商 API 获取可用模型列表。"""
    import httpx

    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"

    resp = httpx.get(
        f"{url}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return sorted([m["id"] for m in data.get("data", []) if m.get("id")])


@router.post("/fetch-available")
def fetch_available_models(body: dict, user: dict = Depends(get_current_user)) -> dict:
    """通过 API Key + URL 获取可用模型列表。"""
    base_url = body.get("base_url", "").strip()
    api_key = body.get("api_key", "").strip()

    if not base_url:
        raise HTTPException(status_code=400, detail="请填写 API 地址")
    if not api_key:
        raise HTTPException(status_code=400, detail="请填写 API Key")

    _validate_url(base_url)

    try:
        models = _fetch_models_from_api(base_url, api_key)
        return {"models": models}
    except HTTPException:
        raise
    except Exception as http_err:
        import httpx
        if isinstance(http_err, httpx.HTTPStatusError):
            status = http_err.response.status_code
            if status == 401:
                msg = "API Key 无效或已过期"
            elif status == 403:
                msg = "API Key 权限不足"
            elif status == 404:
                msg = "API 地址不正确，请检查 URL"
            else:
                msg = f"提供商返回错误 (HTTP {status})"
        else:
            msg = "连接失败，请检查 API 地址是否正确"
        raise HTTPException(status_code=502, detail=msg)


@router.get("/{provider_id}/models")
def fetch_models_for_provider(provider_id: int,
                               user: dict = Depends(get_current_user)) -> dict:
    provider = storage.get_provider_raw(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="提供商不存在")

    try:
        models = _fetch_models_from_api(provider["base_url"], provider["api_key"])
        return {"models": models}
    except Exception as http_err:
        import httpx
        if isinstance(http_err, httpx.HTTPStatusError):
            status = http_err.response.status_code
            if status == 401:
                msg = "API Key 无效或已过期"
            else:
                msg = f"提供商返回错误 (HTTP {status})"
        else:
            msg = "连接失败，请检查 API 地址是否正确"
        raise HTTPException(status_code=502, detail=msg)
