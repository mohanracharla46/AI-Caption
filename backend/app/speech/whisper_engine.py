import whisper
import os
import torch
from typing import Dict, Any, List, Optional
from app.config import DEFAULT_WHISPER_MODEL
from app.transliteration.tenglish_engine import convert_segments

import requests
import hashlib
import time

# In-memory model cache
_LOADED_MODELS: Dict[str, whisper.Whisper] = {}

def ensure_model_downloaded(model_name: str, max_retries: int = 5) -> str:
    """Resiliently downloads Whisper model with range resume and retries."""
    download_root = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    os.makedirs(download_root, exist_ok=True)
    
    url = whisper._MODELS.get(model_name)
    if not url:
        raise ValueError(f"Unknown Whisper model name: {model_name}")
        
    filename = os.path.basename(url)
    model_path = os.path.join(download_root, filename)
    expected_sha256 = url.split("/")[-2]

    # Verify existing file
    if os.path.exists(model_path):
        try:
            with open(model_path, "rb") as f:
                model_bytes = f.read()
            if hashlib.sha256(model_bytes).hexdigest() == expected_sha256:
                return model_path
        except Exception:
            pass

    print(f"Downloading Whisper model '{model_name}' to {model_path} (resumable)...")
    
    for attempt in range(1, max_retries + 1):
        try:
            downloaded = os.path.getsize(model_path) if os.path.exists(model_path) else 0
            headers = {"Range": f"bytes={downloaded}-"} if downloaded > 0 else {}
            
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                if r.status_code == 416:  # Range not satisfiable, file might already be complete
                    break
                r.raise_for_status()
                mode = "ab" if downloaded > 0 and r.status_code == 206 else "wb"
                
                with open(model_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                        if chunk:
                            f.write(chunk)
            
            # Verify file integrity
            with open(model_path, "rb") as f:
                model_bytes = f.read()
            if hashlib.sha256(model_bytes).hexdigest() == expected_sha256:
                print(f"Whisper model '{model_name}' verified successfully.")
                return model_path
            else:
                print(f"Checksum mismatch on attempt {attempt}. Retrying...")
                if os.path.exists(model_path):
                    os.remove(model_path)
        except Exception as e:
            print(f"Download attempt {attempt}/{max_retries} failed: {e}. Retrying in 2s...")
            time.sleep(2)

    return model_path

def get_whisper_model(model_name: Optional[str] = None) -> whisper.Whisper:
    """Loads and caches the Whisper model in memory on CPU or CUDA if available."""
    name = (model_name or DEFAULT_WHISPER_MODEL).lower()
    if name not in _LOADED_MODELS:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Ensure download completes with our resilient downloader
        model_path = ensure_model_downloaded(name)
        print(f"Loading Whisper model '{name}' from '{model_path}' on device '{device}'...")
        _LOADED_MODELS[name] = whisper.load_model(model_path, device=device)
        print(f"Whisper model '{name}' loaded successfully.")
    return _LOADED_MODELS[name]

def transcribe_audio(
    audio_path: str,
    model_name: Optional[str] = None,
    language: str = "te",
    include_word_timestamps: bool = True,
    generate_translation: bool = False
) -> Dict[str, Any]:
    """
    Transcribes audio file using local OpenAI Whisper.
    Returns structured subtitle segments with word timestamps and Tenglish conversions.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = get_whisper_model(model_name)

    # 1. Transcribe in Telugu with domain conditioning prompt
    initial_prompt = (
        "మనం ఇప్పుడు పైథాన్ నేర్చుకుందాం. హలో ఫ్రెండ్స్, ఈరోజు మనం కొత్త వెబ్‌సైట్ మరియు కోడింగ్ ప్రాజెక్ట్ చేద్దాం. "
        "Telugu speech with common English tech words: Python, coding, website, programming, project, video, YouTube, subscribe, app, developer."
    )
    options = {
        "task": "transcribe",
        "verbose": False,
        "initial_prompt": initial_prompt
    }
    if language and language != "auto":
        options["language"] = language

    # Enable word-level timestamps if supported
    if include_word_timestamps:
        try:
            options["word_timestamps"] = True
        except Exception:
            pass

    print(f"Starting Whisper transcription for {audio_path}...")
    result = model.transcribe(audio_path, **options)
    detected_lang = result.get("language", language)
    raw_segments = result.get("segments", [])

    # Format segments
    formatted_segments: List[Dict[str, Any]] = []
    for idx, seg in enumerate(raw_segments):
        seg_text = seg.get("text", "").strip()
        if not seg_text:
            continue

        words_data = []
        if "words" in seg and seg["words"]:
            for w in seg["words"]:
                w_text = w.get("word", "").strip()
                if w_text:
                    words_data.append({
                        "word": w_text,
                        "start": round(w.get("start", seg.get("start", 0)), 2),
                        "end": round(w.get("end", seg.get("end", 0)), 2)
                    })

        formatted_segments.append({
            "id": idx + 1,
            "start": round(seg.get("start", 0), 2),
            "end": round(seg.get("end", 0), 2),
            "text": seg_text,
            "telugu_text": seg_text,
            "words": words_data
        })

    # Optional translation to English
    if generate_translation:
        try:
            trans_result = model.transcribe(audio_path, task="translate", verbose=False)
            trans_segments = trans_result.get("segments", [])
            for i, seg in enumerate(formatted_segments):
                if i < len(trans_segments):
                    seg["english_text"] = trans_segments[i].get("text", "").strip()
        except Exception as e:
            print(f"Translation pass failed or skipped: {e}")

    # Convert to Tenglish
    final_segments = convert_segments(formatted_segments, mode="tenglish")

    return {
        "language": detected_lang,
        "duration": result.get("duration", 0),
        "segments": final_segments
    }
