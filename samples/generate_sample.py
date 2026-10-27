import os
import subprocess
from pathlib import Path
from gtts import gTTS
import sys

# Ensure backend is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.config import FFMPEG_EXE

def generate_sample_telugu_video():
    samples_dir = BASE_DIR / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    text = "మనం ఇప్పుడు పైథాన్ నేర్చుకుందాం. హలో ఫ్రెండ్స్, ఈరోజు మనం కొత్త వెబ్‌సైట్ మరియు కోడింగ్ ప్రాజెక్ట్ చేద్దాం."
    audio_path = samples_dir / "telugu_sample.mp3"
    video_path = samples_dir / "sample_telugu_video.mp4"
    
    print(f"Generating spoken Telugu audio with gTTS: '{text}'...")
    tts = gTTS(text=text, lang="te")
    tts.save(str(audio_path))
    print(f"Audio saved: {audio_path}")
    
    # Generate an MP4 video with a nice sleek dark purple gradient/canvas and the audio track
    print(f"Creating video with FFmpeg: {video_path}...")
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-f", "lavfi",
        "-i", "color=c=0x181028:s=1280x720:d=8:r=30",
        "-i", str(audio_path),
        "-vf", "drawtext=text='Tenglish Auto Caption Sample Video':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=200",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(video_path)
    ]
    
    # If drawtext font is not default, simple color canvas is safe
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        # Fallback without drawtext if fontconfig isn't configured
        cmd_fallback = [
            FFMPEG_EXE,
            "-y",
            "-f", "lavfi",
            "-i", "color=c=0x1a102f:s=1280x720:d=8:r=30",
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(video_path)
        ]
        subprocess.run(cmd_fallback, check=True)
        
    print(f"Sample video created successfully at: {video_path}")
    return video_path

if __name__ == "__main__":
    generate_sample_telugu_video()
