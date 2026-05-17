import os
import re
from typing import Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

MS_BASE = os.environ.get("MODELSCOPE_ENDPOINT", "https://www.modelscope.cn")

_SUPPORTED_HOSTS = frozenset(
    {
        "modelscope.cn",
        "www.modelscope.cn",
        "modelscope.ai",
        "www.modelscope.ai",
    }
)

_PATH_VIEW_RE = re.compile(
    r"^models/(?P<model_id>[^/]+/[^/]+)/file/view/(?P<revision>[^/]+)/(?P<file_path>.+)$"
)
_PATH_RESOLVE_RE = re.compile(
    r"^models/(?P<model_id>[^/]+/[^/]+)/resolve/(?P<revision>[^/]+)/(?P<file_path>.+)$"
)
_API_REPO_RE = re.compile(r"^api/v1/models/(?P<model_id>.+)/repo$")


def ms_download_url(
    model_id: str,
    file_path: str,
    revision: str = "master",
    endpoint: Optional[str] = None,
) -> str:
    base = endpoint or MS_BASE
    return (
        f"{base}/api/v1/models/{model_id}/repo"
        f"?Revision={quote_plus(revision)}&FilePath={quote_plus(file_path)}"
    )


def ms_auth_headers(token: str = "") -> dict:
    token = (token or "").strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def parse_ms_url(url: str) -> tuple[str, str, str]:
    url = (url or "").strip()
    if not url:
        raise ValueError("请提供 ModelScope 链接")

    if not re.match(r"^https?://", url, re.I):
        url = f"{MS_BASE}/{url.lstrip('/')}"

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host and host not in _SUPPORTED_HOSTS:
        raise ValueError(
            f"不支持的域名: {host}，请使用 modelscope.cn 链接"
        )

    path = unquote(parsed.path).strip("/")

    api_match = _API_REPO_RE.match(path)
    if api_match:
        query = parse_qs(parsed.query)
        revision = (query.get("Revision") or ["master"])[0]
        file_path = (query.get("FilePath") or [""])[0]
        if not file_path:
            raise ValueError("API 链接缺少 FilePath 参数")
        return api_match.group("model_id"), file_path, revision

    for pattern in (_PATH_VIEW_RE, _PATH_RESOLVE_RE):
        match = pattern.match(path)
        if match:
            file_path = match.group("file_path").rstrip("/")
            if not file_path:
                raise ValueError("链接中未包含文件路径")
            return (
                match.group("model_id"),
                file_path,
                match.group("revision"),
            )

    raise ValueError(
        "无法解析链接。请粘贴 ModelScope 文件页面地址，例如: "
        "https://www.modelscope.cn/models/AI-ModelScope/stable-diffusion-v1-5/file/view/master/model.safetensors"
    )


def parse_ms_urls(urls_text: str) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for line in (urls_text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parsed = parse_ms_url(line)
        if parsed not in seen:
            seen.add(parsed)
            items.append(parsed)

    if not items:
        raise ValueError("请提供至少一个 ModelScope 链接（每行一个）")

    return items
