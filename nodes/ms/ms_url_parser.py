from ..base_downloader import get_model_dirs
from ..download_progress import BatchProgress
from ..download_utils import DownloadManager
from ..interrupt_utils import throw_if_interrupted
from ..path_utils import resolve_save_target
from .ms_download import MSDownloader
from .ms_utils import ms_auth_headers, ms_download_url, parse_ms_url, parse_ms_urls


class MSUrlParser:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "https://www.modelscope.cn/models/AI-ModelScope/stable-diffusion-v1-5/file/view/master/v1-5-pruned-emaonly.safetensors",
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model_id", "file_path", "revision", "local_path")
    FUNCTION = "parse"
    CATEGORY = "loaders"

    @classmethod
    def VALIDATE_INPUTS(cls, url, **kwargs):
        try:
            parse_ms_url(url)
            return True
        except ValueError as e:
            return str(e)

    def parse(self, url):
        model_id, file_path, revision = parse_ms_url(url)
        model_dirs = get_model_dirs()
        local_path, save_filename = resolve_save_target(
            file_path, "Auto", model_dirs
        )
        print(
            f"[MS URL Parser] {model_id} @ {revision} → "
            f"models/{local_path}/{save_filename}"
        )
        return (model_id, file_path, revision, local_path)


class MSUrlDownloader(MSDownloader):
    """粘贴 ModelScope 文件页链接，自动解析并下载（支持每行一个 URL）。"""

    @classmethod
    def INPUT_TYPES(cls):
        model_dirs = get_model_dirs()
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "https://www.modelscope.cn/models/AI-ModelScope/stable-diffusion-v1-5/file/view/master/v1-5-pruned-emaonly.safetensors",
                    },
                ),
                "local_path": (["Auto"] + model_dirs,),
            },
            "optional": {
                "access_token": (
                    "STRING",
                    {"default": "", "multiline": False, "password": True},
                ),
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
            parse_ms_urls(url)
            return True
        except ValueError as e:
            return str(e)

    def download(
        self,
        url,
        local_path,
        node_id,
        access_token="",
        overwrite=True,
        local_path_override="",
    ):
        self.node_id = node_id
        items = parse_ms_urls(url)
        total = len(items)
        model_dirs = get_model_dirs()
        headers = ms_auth_headers(access_token)

        for i, (model_id, file_path, revision) in enumerate(items):
            throw_if_interrupted()
            final_path, save_filename = resolve_save_target(
                file_path, local_path, model_dirs, local_path_override
            )

            print(
                f"[MS URL Downloader] ({i + 1}/{total}) {model_id} @ {revision} "
                f"→ models/{final_path}/{save_filename}"
            )

            save_path = self.prepare_download_path(final_path, save_filename)
            download_url = ms_download_url(model_id, file_path, revision)
            is_last = i == total - 1

            self.handle_download(
                DownloadManager.download_with_progress,
                save_path=save_path,
                filename=save_filename,
                overwrite=overwrite,
                url=download_url,
                progress_callback=BatchProgress(self, i, total),
                download_filename=save_filename,
                headers=headers,
                finalize=is_last,
            )
            if not is_last:
                self.set_progress(((i + 1) / total) * 100.0)

        return {}
