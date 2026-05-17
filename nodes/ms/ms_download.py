from ..base_downloader import BaseModelDownloader, get_model_dirs
from ..download_utils import DownloadManager
from .ms_utils import ms_auth_headers, ms_download_url


class MSDownloader(BaseModelDownloader):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_id": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "AI-ModelScope/stable-diffusion-v1-5",
                    },
                ),
                "file_path": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "v1-5-pruned-emaonly.safetensors",
                    },
                ),
                "local_path": (get_model_dirs(),),
            },
            "optional": {
                "revision": ("STRING", {"default": "master", "multiline": False}),
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

    def download(
        self,
        model_id,
        file_path,
        local_path,
        node_id,
        revision="master",
        access_token="",
        overwrite=True,
        local_path_override="",
    ):
        if not model_id or not file_path:
            print(
                f"Missing required values: model_id='{model_id}', file_path='{file_path}'"
            )
            return {}

        final_path = local_path_override if local_path_override else local_path
        print(
            f"[MS Downloader] {model_id} @ {revision or 'master'} "
            f"→ {file_path} → models/{final_path}"
        )
        self.node_id = node_id
        save_path = self.prepare_download_path(final_path, file_path)
        url = ms_download_url(model_id, file_path, revision or "master")
        save_name = file_path.split("/")[-1]

        return self.handle_download(
            DownloadManager.download_with_progress,
            save_path=save_path,
            filename=save_name,
            overwrite=overwrite,
            url=url,
            progress_callback=self,
            download_filename=save_name,
            headers=ms_auth_headers(access_token),
        )
