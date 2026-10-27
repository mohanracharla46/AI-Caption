import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.speech.audio_extractor import extract_audio
from app.speech.whisper_engine import transcribe_audio
from app.transliteration.tenglish_engine import convert_segments, to_tenglish
from app.video.ffmpeg_subtitles import generate_srt_content, generate_vtt_content, burn_subtitles_to_video

def run_test():
    print("=" * 60)
    print("🧪 Running End-to-End Tenglish Caption Generator Test")
    print("=" * 60)
    
    video_path = BASE_DIR / "samples" / "sample_telugu_video.mp4"
    if not video_path.exists():
        print(f"❌ Sample video not found at {video_path}")
        return False
        
    print(f"1️⃣ Video found: {video_path} ({video_path.stat().st_size} bytes)")
    
    # Step 1: Extract Audio
    wav_path = BASE_DIR / "temp" / "test_audio.wav"
    print(f"2️⃣ Extracting 16kHz WAV audio to: {wav_path}...")
    extract_audio(str(video_path), str(wav_path))
    print(f"   Audio extracted successfully ({wav_path.stat().st_size} bytes)")
    
    # Step 2: Whisper speech recognition
    print("3️⃣ Transcribing audio with local Whisper (tiny/base)...")
    result = transcribe_audio(str(wav_path), model_name="tiny", language="te")
    print(f"   Detected Language: {result['language']}, Duration: {result['duration']:.2f}s")
    print(f"   Segments Count: {len(result['segments'])}")
    for s in result['segments']:
        print(f"   [{s['start']:.2f}s - {s['end']:.2f}s] Telugu: {s.get('telugu_text')}")
        print(f"   [{s['start']:.2f}s - {s['end']:.2f}s] Tenglish: {s.get('text')}")
        if s.get('words'):
            words_str = " | ".join(f"{w['word']} ({w['start']}-{w['end']})" for w in s['words'])
            print(f"   Words: {words_str}")
            
    # Step 3: Format SRT & VTT
    print("4️⃣ Generating Subtitle Files (SRT & VTT)...")
    srt = generate_srt_content(result['segments'])
    vtt = generate_vtt_content(result['segments'])
    print(f"   SRT length: {len(srt)} chars")
    print(f"   VTT length: {len(vtt)} chars")
    
    # Step 4: Burn Subtitles to Video
    print("5️⃣ Testing Video Burning with Reels-Style Captions via FFmpeg...")
    test_out_video = BASE_DIR / "exports" / "test_captioned_video.mp4"
    style = {
        "preset": "reels_highlight",
        "font_name": "Arial",
        "font_size": 28,
        "primary_color": "#FFFFFF",
        "highlight_color": "#A855F7",
        "outline_color": "#000000",
        "outline_width": 2.5,
        "is_reels": True,
        "position": "bottom"
    }
    burn_subtitles_to_video(
        video_path=str(video_path),
        output_video_path=str(test_out_video),
        segments=result['segments'],
        style=style
    )
    print(f"   Burned video created: {test_out_video} ({test_out_video.stat().st_size} bytes)")
    
    print("=" * 60)
    print("✅ All End-to-End Pipeline Steps Passed Successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_test()
    if not success:
        sys.exit(1)
