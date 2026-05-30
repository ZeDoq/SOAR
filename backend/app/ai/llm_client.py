"""LLM client wrapper with multi-provider support.

支持 OpenAI、DeepSeek、MiMo、通义千问等 OpenAI 兼容 API。
提供商配置存储在数据库的 llm_providers 表中，环境变量作为 fallback。
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_clients: dict = {}


def _normalize_base_url(url: str) -> str:
    """确保 base_url 格式正确。"""
    if not url:
        return url
    url = url.rstrip("/")
    # 如果 URL 不以 /v1 结尾，加上 /v1（OpenAI SDK 需要）
    # 但如果 URL 已经包含 /v1，则不重复添加
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


def _create_client(api_key: str, base_url: str = None):
    """创建 OpenAI 客户端。"""
    try:
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = _normalize_base_url(base_url)
        return OpenAI(**kwargs)
    except ImportError:
        logger.error("openai 包未安装，请运行 pip install openai")
        return None
    except Exception as e:
        logger.error("创建 OpenAI 客户端失败: %s", e)
        return None


def _get_client_from_env():
    """从环境变量获取客户端（向后兼容）。"""
    key = "_env"
    if key in _clients:
        return _clients[key]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", None)
    client = _create_client(api_key, base_url)
    if client:
        _clients[key] = client
    return client


def _get_client_for_provider(provider_id: int = None):
    """获取指定提供商的客户端。"""
    if provider_id:
        if provider_id in _clients:
            return _clients[provider_id]
        try:
            from .. import storage
            provider = storage.get_provider_raw(provider_id)
        except Exception:
            provider = None
        if provider and provider.get("api_key"):
            client = _create_client(provider["api_key"], provider.get("base_url"))
            if client:
                _clients[provider_id] = client
            return client
        return None

    # 无指定 provider：先查 DB 默认，再 fallback 到环境变量
    try:
        from .. import storage
        default = storage.get_default_provider()
    except Exception:
        default = None

    if default and default.get("api_key"):
        cache_key = f"db_{default['id']}"
        if cache_key in _clients:
            return _clients[cache_key]
        client = _create_client(default["api_key"], default.get("base_url"))
        if client:
            _clients[cache_key] = client
        return client

    return _get_client_from_env()


def _get_model_name(provider_id: int = None) -> str:
    """获取模型名称。"""
    if provider_id:
        try:
            from .. import storage
            provider = storage.get_provider_raw(provider_id)
            if provider:
                return provider["model_name"]
        except Exception:
            pass

    try:
        from .. import storage
        default = storage.get_default_provider()
        if default:
            return default["model_name"]
    except Exception:
        pass

    return os.getenv("OPENAI_MODEL", "gpt-4.1")


def clear_cache():
    """清除所有客户端缓存（配置变更后调用）。"""
    _clients.clear()


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.3,
         provider_id: int = None) -> str:
    """发送聊天请求。无 API Key 时返回空字符串。"""
    client = _get_client_for_provider(provider_id)
    if not client:
        logger.warning("无可用 LLM 提供商，使用规则引擎兜底")
        return ""
    model = _get_model_name(provider_id)
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        # 脱敏异常信息，避免泄露 API Key
        err_msg = str(e)
        if api_key and api_key in err_msg:
            err_msg = err_msg.replace(api_key, "***")
        logger.error("LLM 调用失败 (model=%s): %s", model, err_msg[:200])
        return ""


def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.1,
              provider_id: int = None) -> Optional[dict]:
    """聊天并解析 JSON 响应。失败返回 None。"""
    raw = chat(system_prompt, user_prompt, temperature, provider_id)
    if not raw:
        return None
    try:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("LLM 响应解析 JSON 失败: %s", raw[:200])
        return None


def test_provider(provider_id: int) -> dict:
    """测试提供商连通性。返回 {ok, message, model}。"""
    try:
        from .. import storage
        provider = storage.get_provider_raw(provider_id)
    except Exception as e:
        return {"ok": False, "message": f"读取提供商配置失败: {e}", "model": None}

    if not provider:
        return {"ok": False, "message": "提供商不存在", "model": None}

    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "")
    model = provider.get("model_name", "")

    if not api_key:
        return {"ok": False, "message": "API Key 为空", "model": model}
    if not base_url:
        return {"ok": False, "message": "API 地址为空", "model": model}
    if not model:
        return {"ok": False, "message": "模型名称为空", "model": model}

    client = _create_client(api_key, base_url)
    if not client:
        return {"ok": False, "message": "创建客户端失败，请检查 openai 包是否安装", "model": model}

    normalized_url = _normalize_base_url(base_url)
    try:
        resp = client.chat.completions.create(
            model=model, temperature=0, max_tokens=5,
            messages=[{"role": "user", "content": "Hi"}],
        )
        return {"ok": True, "message": f"连接成功 (model={model})", "model": model}
    except Exception as e:
        err = str(e)
        # 提供更友好的错误信息
        if "401" in err or "Unauthorized" in err or "auth" in err.lower():
            msg = "API Key 无效或已过期"
        elif "404" in err or "NotFound" in err or "not found" in err.lower():
            msg = f"模型 '{model}' 不存在，请检查模型名称是否正确"
        elif "429" in err:
            msg = "请求频率超限，请稍后重试"
        elif "timeout" in err.lower() or "connect" in err.lower():
            msg = f"连接超时，请检查 API 地址是否正确: {normalized_url}"
        else:
            msg = err[:200]
        logger.warning("测试连接失败 (url=%s, model=%s): %s", normalized_url, model, msg)
        return {"ok": False, "message": msg, "model": model}
