import whisper
import os
import re
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

def is_hallucinated(text: str) -> bool:
    """Checks if text contains non-Telugu, non-English foreign scripts (Chinese, Cyrillic, Arabic, etc.)."""
    for ch in text:
        c = ord(ch)
        if (0x4E00 <= c <= 0x9FFF) or (0x0400 <= c <= 0x04FF) or (0x0600 <= c <= 0x06FF) or (0x3040 <= c <= 0x30FF) or (0xAC00 <= c <= 0xD7AF):
            return True
    return False

def is_repetitive(text: str) -> bool:
    """Detects decoder looping such as నినినిని or repeating syllables."""
    if not text or len(text) < 6:
        return False
    # Check for repeated single character 4+ times
    if re.search(r"(.)\1{3,}", text):
        return True
    # Check for 2-4 character syllable repeated 3+ times
    for n in range(2, 5):
        if re.search(rf"(.{{{n}}})\1{{2,}}", text):
            return True
    return False

def is_invalid_output(segs: list) -> bool:
    if not segs:
        return True
    if any(is_hallucinated(s.get("text", "")) for s in segs):
        return True
    if any(is_repetitive(s.get("text", "")) for s in segs):
        return True
    return False

def sanitize_text(text: str) -> str:
    """Removes foreign hallucinated Unicode characters (Chinese, Cyrillic, Arabic, etc.) leaving Telugu, English, punctuation."""
    cleaned = []
    for ch in text:
        c = ord(ch)
        if (0x4E00 <= c <= 0x9FFF) or (0x0400 <= c <= 0x04FF) or (0x0600 <= c <= 0x06FF) or (0x3040 <= c <= 0x30FF) or (0xAC00 <= c <= 0xD7AF):
            continue
        cleaned.append(ch)
    return "".join(cleaned).strip()

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

    options = {
        "task": "transcribe",
        "verbose": False,
        "condition_on_previous_text": False,
        "compression_ratio_threshold": 2.4,
        "no_speech_threshold": 0.6
    }
    if language == "translate":
        options["task"] = "translate"
        options["language"] = "te"
    elif language and language != "auto":
        options["language"] = language

    # Attempt transcription with word timestamps if requested
    raw_segments = []
    result = {}

    if include_word_timestamps:
        try:
            opts_with_words = dict(options)
            opts_with_words["word_timestamps"] = True
            print(f"Transcribing {audio_path} with word timestamps (language={language})...")
            result = model.transcribe(audio_path, **opts_with_words)
            raw_segments = result.get("segments", [])
        except Exception as e:
            print(f"Word timestamp pass failed or timed out: {e}")
            raw_segments = []

    # Check if word timestamp pass collapsed or produced invalid/repetitive output
    has_invalid = is_invalid_output(raw_segments)
    has_collapsed = raw_segments and (len(raw_segments) <= 2 and (raw_segments[-1].get("end", 0) - raw_segments[0].get("start", 0) > 15))
    if has_invalid or has_collapsed:
        print("Notice: Word timestamp pass collapsed or produced invalid output. Falling back to standard pass...")
        raw_segments = []

    # Resilient Fallback 1: If word_timestamps yielded 0 segments or failed, run standard segment transcription
    if not raw_segments:
        print(f"Running standard segment transcription for {audio_path} (language={language})...")
        result = model.transcribe(audio_path, **options)
        raw_segments = result.get("segments", [])

    # Resilient Fallback 2: If language was forced to 'te' and returned invalid/repetitive output, auto-detect language
    if is_invalid_output(raw_segments) and language == "te":
        print(f"Telugu-specific pass produced invalid/repetitive output. Retrying with auto language detection...")
        fallback_opts = dict(options)
        fallback_opts.pop("language", None)
        result = model.transcribe(audio_path, **fallback_opts)
        raw_segments = result.get("segments", [])

    # Resilient Fallback 3: If still invalid or repeating, translate to English for coherent, natural captions
    if is_invalid_output(raw_segments):
        print("Notice: Transcribe output still invalid/repetitive. Running English translation task for accurate captions...")
        translate_opts = dict(options)
        translate_opts["task"] = "translate"
        translate_opts["language"] = "te"
        result = model.transcribe(audio_path, **translate_opts)
        raw_segments = result.get("segments", [])

    detected_lang = result.get("language", language or "te")

    # Format segments
    formatted_segments: List[Dict[str, Any]] = []
    for idx, seg in enumerate(raw_segments):
        seg_text = sanitize_text(seg.get("text", "").strip())
        if not seg_text:
            continue

        start_time = round(float(seg.get("start", 0)), 2)
        end_time = round(float(seg.get("end", start_time + 1.0)), 2)
        if end_time <= start_time:
            end_time = start_time + 1.0

        words_data = []
        if "words" in seg and seg["words"]:
            for w in seg["words"]:
                w_text = w.get("word", "").strip()
                if w_text:
                    words_data.append({
                        "word": w_text,
                        "start": round(float(w.get("start", start_time)), 2),
                        "end": round(float(w.get("end", end_time)), 2)
                    })

        # If word timestamps were not generated by Whisper, distribute words evenly across duration
        if not words_data:
            tokens = seg_text.split()
            if tokens:
                duration = max(0.5, end_time - start_time)
                word_dur = duration / len(tokens)
                for w_idx, tok in enumerate(tokens):
                    w_s = round(start_time + w_idx * word_dur, 2)
                    w_e = round(min(end_time, w_s + word_dur), 2)
                    words_data.append({
                        "word": tok,
                        "start": w_s,
                        "end": w_e
                    })

        formatted_segments.append({
            "id": idx + 1,
            "start": start_time,
            "end": end_time,
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
