class BatchProgress:
    def __init__(self, downloader, index: int, total: int):
        self._downloader = downloader
        self._index = index
        self._total = total

    def set_progress(self, progress: float):
        overall = ((self._index + progress / 100.0) / self._total) * 100.0
        self._downloader.set_progress(overall)
