from .nodes.auto.downloader import AutoModelDownloader
from .nodes.cai.cai_download import CivitAIDownloader
from .nodes.hf.hf_download import HFDownloader
from .nodes.hf.hf_url_parser import HFUrlDownloader, HFUrlParser
from .nodes.ms.ms_download import MSDownloader
from .nodes.ms.ms_url_parser import MSUrlDownloader, MSUrlParser

NODE_CLASS_MAPPINGS = {
    "HF URL Downloader": HFUrlDownloader,
    "HF URL Parser": HFUrlParser,
    "HF Downloader": HFDownloader,
    "MS URL Downloader": MSUrlDownloader,
    "MS URL Parser": MSUrlParser,
    "MS Downloader": MSDownloader,
    "Auto Model Downloader": AutoModelDownloader,
    "CivitAI Downloader": CivitAIDownloader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HF URL Downloader": "HF URL Download",
    "HF URL Parser": "HF URL Parser",
    "HF Downloader": "HF Download",
    "MS URL Downloader": "MS URL Download",
    "MS URL Parser": "MS URL Parser",
    "MS Downloader": "MS Download",
    "Auto Model Downloader": "Auto Model Finder (Experimental)",
    "CivitAI Downloader": "CivitAI Download",
}

# Relative path required by ComfyUI's frontend extension loader.
# See: https://docs.comfy.org/custom-nodes/js/javascript_overview
WEB_DIRECTORY = "./js"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
