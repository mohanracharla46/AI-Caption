import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import FFMPEG_EXE
from app.video.ass_builder import generate_ass_subtitles

def format_srt_time(seconds: float) -> str:
    """Formats seconds to SRT format: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def format_vtt_time(seconds: float) -> str:
    """Formats seconds to WebVTT format: HH:MM:SS.mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

def generate_srt_content(segments: List[Dict[str, Any]]) -> str:
    """Generates standard SRT subtitle string."""
    blocks = []
    idx = 1
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        start_str = format_srt_time(float(seg.get("start", 0)))
        end_str = format_srt_time(float(seg.get("end", 0)))
        blocks.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")
        idx += 1
    return "\n".join(blocks)

def generate_vtt_content(segments: List[Dict[str, Any]]) -> str:
    """Generates standard WebVTT subtitle string."""
    blocks = ["WEBVTT\n"]
    idx = 1
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        start_str = format_vtt_time(float(seg.get("start", 0)))
        end_str = format_vtt_time(float(seg.get("end", 0)))
        blocks.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")
        idx += 1
    return "\n".join(blocks)

def escape_ffmpeg_filter_path(path_str: str) -> str:
    r"""
    Escapes a Windows path for use in FFmpeg filter graph (e.g. subtitles='C\:/...').
    """
    # Replace backslashes with forward slashes
    clean = path_str.replace("\\", "/")
    # Escape colon (e.g. C: -> C\:)
    clean = clean.replace(":", r"\:")
    # Escape single quotes
    clean = clean.replace("'", r"\'")
    return clean

import re

def get_video_resolution(video_path: str) -> tuple:
    """Detects video width and height using FFmpeg."""
    cmd = [FFMPEG_EXE, "-i", str(video_path)]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        match = re.search(r"Video:.*?(\d{3,4})x(\d{3,4})", proc.stderr or "")
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception as e:
        print(f"Notice: Failed to detect video resolution ({e}), using default 1280x720.")
    return 1280, 720

def burn_subtitles_to_video(
    video_path: str,
    output_video_path: str,
    segments: List[Dict[str, Any]],
    style: Optional[Dict[str, Any]] = None,
    timeout: int = 300
) -> str:
    """
    Renders styled subtitles onto the video permanently using FFmpeg libass subtitle filter.
    """
    in_video = Path(video_path).resolve()
    out_video = Path(output_video_path).resolve()

    if not in_video.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    # Detect video dimensions for proper subtitle scaling
    v_width, v_height = get_video_resolution(str(in_video))

    # Generate ASS file in same directory to avoid escaping issues
    ass_path = in_video.parent / f"{in_video.stem}_subtitles.ass"
    ass_content = generate_ass_subtitles(segments, style, video_width=v_width, video_height=v_height)
    
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # Use relative filename with cwd set to parent directory, or properly escaped path
    escaped_ass = escape_ffmpeg_filter_path(str(ass_path))

    # FFmpeg command to burn subtitles
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-i", str(in_video),
        "-vf", f"subtitles='{escaped_ass}'",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "copy",
        str(out_video)
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=True
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Video burning timed out after {timeout} seconds.")
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg subtitle burning failed: {err}")

    if not out_video.exists() or out_video.stat().st_size == 0:
        raise RuntimeError("Burned video file was not created or is empty.")

    return str(out_video)
