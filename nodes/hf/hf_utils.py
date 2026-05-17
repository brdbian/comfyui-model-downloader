import os
from tqdm import tqdm
import requests

from ..interrupt_utils import throw_if_interrupted

HF_MIRROR_BASE = "https://hf-mirror.com"


def hf_download_url(repo_id, filename, revision="main"):
    return f"{HF_MIRROR_BASE}/{repo_id}/resolve/{revision}/{filename}"


def configure_hf_mirror():
    os.environ.setdefault("HF_ENDPOINT", HF_MIRROR_BASE)


def download_hf(repo_id, filename, save_path, overwrite=False, progress_callback=None):
    URL = hf_download_url(repo_id, filename)
    
    # Get file size first
    response = requests.get(URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Create the full file path
    full_file_path = os.path.join(save_path, filename)
    
    chunk_size = 1024 * 1024  # 1MB chunks
    downloaded = 0

    try:
        throw_if_interrupted()
        with open(full_file_path, "wb") as file:
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=filename, leave=True) as pbar:
                for data in response.iter_content(chunk_size=chunk_size):
                    throw_if_interrupted()
                    if not data:
                        continue
                    size = file.write(data)
                    downloaded += size
                    pbar.update(size)

                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100.0
                        progress_callback.set_progress(progress)
    except BaseException:
        if os.path.exists(full_file_path):
            os.remove(full_file_path)
        raise
    finally:
        response.close()

    return True