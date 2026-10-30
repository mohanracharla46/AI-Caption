import json
import uuid
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.config import UPLOADS_DIR, EXPORTS_DIR

class JobManager:
    """Manages video processing jobs and their state."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        # Pre-load existing jobs if any
        self._load_all_from_disk()

    def _job_dir(self, job_id: str) -> Path:
        p = UPLOADS_DIR / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _job_meta_file(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def _load_all_from_disk(self):
        if not UPLOADS_DIR.exists():
            return
        for sub in UPLOADS_DIR.iterdir():
            if sub.is_dir():
                meta = sub / "job.json"
                if meta.exists():
                    try:
                        with open(meta, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            self._jobs[sub.name] = data
                    except Exception:
                        pass

    def create_job(self, original_filename: str, file_ext: str) -> str:
        job_id = str(uuid.uuid4())[:8]
        job_folder = self._job_dir(job_id)
        video_filename = f"source{file_ext}"
        video_path = str(job_folder / video_filename)

        job_data = {
            "job_id": job_id,
            "original_filename": original_filename,
            "video_filename": video_filename,
            "video_path": video_path,
            "audio_path": None,
            "status": "QUEUED",
            "stage_message": "Uploaded. Waiting to process...",
            "progress": 5,
            "segments": [],
            "caption_mode": "tenglish",
            "style": {
                "font_name": "Arial",
                "font_size": 24,
                "primary_color": "#FFFFFF",
                "highlight_color": "#A855F7",
                "outline_color": "#000000",
                "background_color": "#000000",
                "background_alpha": 128,
                "outline_width": 2.0,
                "shadow_offset": 1.0,
                "position": "bottom",
                "box_background": False,
                "is_reels": False,
                "preset": "reels_highlight",
                "word_zoom": 1.25,
                "uppercase": False
            },
            "burned_video_path": None,
            "burn_progress": 0,
            "burn_status": "IDLE",
            "error_message": None,
            "created_at": time.time(),
            "updated_at": time.time()
        }

        self._jobs[job_id] = job_data
        self.save_job(job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        meta = self._job_meta_file(job_id)
        if meta.exists():
            try:
                with open(meta, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._jobs[job_id] = data
                    return data
            except Exception:
                pass
        if job_id in self._jobs:
            return self._jobs[job_id]
        return None

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        job = self.get_job(job_id)
        if not job:
            return None
        job.update(updates)
        job["updated_at"] = time.time()
        self.save_job(job_id)
        return job

    def save_job(self, job_id: str):
        job = self._jobs.get(job_id)
        if not job:
            return
        meta = self._job_meta_file(job_id)
        try:
            with open(meta, "w", encoding="utf-8") as f:
                json.dump(job, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving job {job_id}: {e}")

    def update_segments(self, job_id: str, segments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return self.update_job(job_id, {"segments": segments})

job_manager = JobManager()
