import re
from urllib.parse import unquote, urlparse

from ..base_downloader import get_model_dirs
from ..download_progress import BatchProgress
from ..download_utils import DownloadManager
from ..interrupt_utils import throw_if_interrupted
from ..path_utils import resolve_save_target
from .hf_download import HFDownloader
from .hf_utils import hf_download_url

_SUPPORTED_HOSTS = frozenset(
    {"huggingface.co", "www.huggingface.co", "hf-mirror.com", "www.hf-mirror.com"}
)

_PATH_RE = re.compile(
    r"^(?P<repo_id>[^/]+/[^/]+)/(?:blob|resolve|tree)/(?P<revision>[^/]+)/(?P<filename>.+)$"
)


def parse_hf_url(url: str) -> tuple[str, str, str]:
    url = (url or "").strip()
    if not url:
        raise ValueError("请提供 Hugging Face 链接")

    if not re.match(r"^https?://", url, re.I):
        url = f"https://huggingface.co/{url.lstrip('/')}"

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host and host not in _SUPPORTED_HOSTS:
        raise ValueError(
            f"不支持的域名: {host}，请使用 huggingface.co 或 hf-mirror.com 链接"
        )

    path = unquote(parsed.path).strip("/")
    if path.startswith("datasets/"):
        raise ValueError("暂不支持 datasets 链接，请使用模型仓库的文件页面地址")

    match = _PATH_RE.match(path)
    if not match:
        raise ValueError(
            "无法解析链接。请粘贴文件页面地址（含 /blob/、/resolve/ 或 /tree/），"
            "例如: https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/text_encoders/qwen_3_4b.safetensors"
        )

    filename = match.group("filename").rstrip("/")
    if not filename:
        raise ValueError("链接中未包含文件路径")

    return match.group("repo_id"), filename, match.group("revision")


def parse_hf_urls(urls_text: str) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for line in (urls_text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parsed = parse_hf_url(line)
        if parsed not in seen:
            seen.add(parsed)
            items.append(parsed)

    if not items:
        raise ValueError("请提供至少一个 Hugging Face 链接（每行一个）")

    return items


class HFUrlParser:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/text_encoders/qwen_3_4b.safetensors",
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("repo_id", "filename", "revision", "local_path")
    FUNCTION = "parse"
    CATEGORY = "loaders"

    @classmethod
    def VALIDATE_INPUTS(cls, url, **kwargs):
        try:
            parse_hf_url(url)
            return True
        except ValueError as e:
            return str(e)

    def parse(self, url):
        repo_id, repo_filename, revision = parse_hf_url(url)
        model_dirs = get_model_dirs()
        local_path, save_filename = resolve_save_target(
            repo_filename, "Auto", model_dirs
        )
        print(
            f"[HF URL Parser] {repo_id} @ {revision} → "
            f"models/{local_path}/{save_filename}"
        )
        return (repo_id, repo_filename, revision, local_path)


class HFUrlDownloader(HFDownloader):
    """粘贴 Hugging Face 文件页链接，自动解析并下载（支持每行一个 URL）。"""

    @classmethod
    def INPUT_TYPES(cls):
        model_dirs = get_model_dirs()
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/text_encoders/qwen_3_4b.safetensors",
                    },
                ),
                "local_path": (["Auto"] + model_dirs,),
            },
            "optional": {
                "overwrite": ("BOOLEAN", {"default": True}),
                "local_path_override": ("STRING", {"default": ""}),
            },
            "hidden": {
                "node_id": "UNIQUE_ID",
            },
        }

    FUNCTION = "download"

    @classmethod
    def VALIDATE_INPUTS(cls, url, **kwargs):
        try:
            parse_hf_urls(url)
            return True
        except ValueError as e:
            return str(e)

    def download(self, url, local_path, node_id, overwrite=True, local_path_override=""):
        self.node_id = node_id
        items = parse_hf_urls(url)
        total = len(items)
        model_dirs = get_model_dirs()

        for i, (repo_id, repo_filename, revision) in enumerate(items):
            throw_if_interrupted()
            final_path, save_filename = resolve_save_target(
                repo_filename, local_path, model_dirs, local_path_override
            )

            print(
                f"[HF URL Downloader] ({i + 1}/{total}) {repo_id} @ {revision} "
                f"→ models/{final_path}/{save_filename}"
            )

            save_path = self.prepare_download_path(final_path, save_filename)
            download_url = hf_download_url(repo_id, repo_filename, revision)
            is_last = i == total - 1

            self.handle_download(
                DownloadManager.download_with_progress,
                save_path=save_path,
                filename=save_filename,
                overwrite=overwrite,
                url=download_url,
                progress_callback=BatchProgress(self, i, total),
                download_filename=save_filename,
                finalize=is_last,
            )
            if not is_last:
                self.set_progress(((i + 1) / total) * 100.0)

        return {}
