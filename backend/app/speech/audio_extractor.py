import subprocess
import os
from pathlib import Path
from typing import Optional
from app.config import FFMPEG_EXE

def extract_audio(video_path: str, output_wav_path: Optional[str] = None, timeout: int = 120) -> str:
    """
    Extracts a 16kHz mono WAV audio file from the video using FFmpeg.
    This format is optimal for Whisper speech recognition.
    """
    video_p = Path(video_path)
    if not video_p.exists():
        raise FileNotFoundError(f"Input video file not found: {video_path}")

    if output_wav_path is None:
        output_wav_path = str(video_p.with_suffix(".wav"))

    # FFmpeg command: extract audio, 16000 Hz, 1 channel (mono), 16-bit PCM WAV
    cmd = [
        FFMPEG_EXE,
        "-y",               # Overwrite output
        "-i", str(video_p), # Input video
        "-vn",              # Disable video recording
        "-acodec", "pcm_s16le",
        "-ar", "16000",     # 16kHz
        "-ac", "1",         # mono
        str(output_wav_path)
    ]

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=True
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Audio extraction timed out after {timeout} seconds.")
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg audio extraction failed: {err_msg}")

    if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
        raise RuntimeError("Extracted audio file is empty or missing.")

    return output_wav_path

def get_media_duration(file_path: str) -> float:
    """Gets duration in seconds of media file using FFmpeg/ffprobe if possible."""
    # We can use ffmpeg -i to inspect duration
    cmd = [FFMPEG_EXE, "-i", str(file_path)]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        # Look for "Duration: 00:01:23.45"
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                time_str = line.split("Duration:")[1].split(",")[0].strip()
                parts = time_str.split(":")
                if len(parts) == 3:
                    hours = float(parts[0])
                    mins = float(parts[1])
                    secs = float(parts[2])
                    return hours * 3600 + mins * 60 + secs
    except Exception:
        pass
    return 0.0
