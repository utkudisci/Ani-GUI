import os
import subprocess
import shutil
import requests
import threading
from pathlib import Path

class DownloadManager:
    def __init__(self):
        self.download_dir = os.path.join(os.path.expanduser("~"), "ani-cli-downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        self.has_aria2 = shutil.which("aria2c") is not None
        print(f"⬇️ Download Manager initialized. aria2c detected: {self.has_aria2}")
        print(f"📂 Download directory: {self.download_dir}")

    def download_episode(self, url, anime_title, episode_no, on_progress=None, on_complete=None, on_error=None):
        """Start a download in a separate thread"""
        filename = f"{self._sanitize_filename(anime_title)} - Episode {episode_no}.mp4"
        filepath = os.path.join(self.download_dir, filename)
        
        threading.Thread(
            target=self._download_worker,
            args=(url, filepath, on_progress, on_complete, on_error),
            daemon=True
        ).start()

    def _download_worker(self, url, filepath, on_progress, on_complete, on_error):
        try:
            if self.has_aria2:
                self._download_aria2(url, filepath, on_progress)
            else:
                self._download_requests(url, filepath, on_progress)
            
            if on_complete:
                on_complete(filepath)
                
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _download_aria2(self, url, filepath, on_progress):
        print(f"🚀 Starting aria2c download: {filepath}")
        cmd = [
            "aria2c", 
            url, 
            "-o", os.path.basename(filepath),
            "-d", os.path.dirname(filepath),
            "--split=16",
            "--max-connection-per-server=16",
            "--min-split-size=1M",
            "--stream-piece-selector=geom",
            "--summary-interval=1",
            "--referer=https://allmanga.to" 
        ]
        
        # Aria2c output parsing is complex for progress bar, 
        # for MVP we just wait for it to finish or show indiscriminate loading.
        # Capturing output would require Popen and reading stdout.
        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        if proc.returncode != 0:
            raise Exception(f"Aria2c failed: {proc.stderr}")

    def _download_requests(self, url, filepath, on_progress):
        print(f"🐢 Starting requests download (fallback): {filepath}")
        headers = {"Referer": "https://allmanga.to"}
        
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                if total_length == 0:
                    f.write(r.content)
                else:
                    dl = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            dl += len(chunk)
                            # if on_progress:
                            #     on_progress(dl / total_length)

    def _sanitize_filename(self, name):
        return "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()

download_manager = DownloadManager()
