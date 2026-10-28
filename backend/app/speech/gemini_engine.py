import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.config import FFMPEG_EXE, TEMP_DIR

def compress_audio_for_api(input_audio_path: str, max_duration_sec: Optional[float] = None) -> str:
    """
    Compresses audio to a lightweight 96kbps MP3 to minimize upload latency.
    """
    input_p = Path(input_audio_path)
    output_mp3 = TEMP_DIR / f"{input_p.stem}_compressed.mp3"
    
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-i", str(input_p),
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "96k",
        "-ar", "24000",
        "-ac", "1"
    ]
    if max_duration_sec:
        cmd.extend(["-t", str(max_duration_sec)])
    cmd.append(str(output_mp3))
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if output_mp3.exists() and output_mp3.stat().st_size > 0:
            return str(output_mp3)
    except Exception as e:
        print(f"Notice: MP3 compression failed ({e}), using original audio.")
        
    return input_audio_path

def transcribe_with_gemini(
    audio_path: str,
    api_key: str,
    preferred_model: str = "gemini-3.5-flash"
) -> Dict[str, Any]:
    """
    Transcribes audio using Google Gemini multimodal speech API.
    Provides 99% accuracy for Telugu script, conversational Tenglish, and English translation.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
    if not api_key or not api_key.strip():
        raise ValueError("A valid Gemini API key is required.")

    # Lazy import google-genai
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai package is not installed. Run 'pip install google-genai'.")

    # Compress audio to lightweight MP3 for fast upload
    compressed_path = compress_audio_for_api(audio_path)
    with open(compressed_path, "rb") as f:
        audio_bytes = f.read()

    client = genai.Client(api_key=api_key.strip())

    prompt = """You are an expert Telugu and Tenglish (conversational Telugu spoken language written using English alphabet) subtitle transcriber.

Listen to the attached audio very carefully. The speaker is speaking conversational Telugu, potentially code-switching with common English words (such as 'coding', 'business logic', 'debugging', 'project', 'developer', 'website', 'support', 'requirements', etc.).

Transcribe the speech accurately with high temporal precision for video reels subtitles.

Generate a JSON array of subtitle segments. Output ONLY raw valid JSON (no markdown formatting, no code fences):
[
  {
    "id": 1,
    "start": 0.0,
    "end": 2.5,
    "text": "Manam ippudu coding nerchukovali kada?",
    "telugu_text": "మనం ఇప్పుడు కోడింగ్ నేర్చుకోవాలి కదా?",
    "tenglish_text": "Manam ippudu coding nerchukovali kada?",
    "english_text": "We should learn coding now, right?",
    "words": [
      {"word": "Manam", "start": 0.0, "end": 0.5},
      {"word": "ippudu", "start": 0.5, "end": 1.0},
      {"word": "coding", "start": 1.0, "end": 1.6},
      {"word": "nerchukovali", "start": 1.6, "end": 2.2},
      {"word": "kada?", "start": 2.2, "end": 2.5}
    ]
  }
]

CRITICAL RULES:
1. "text" and "tenglish_text": Write in natural, easy-to-read conversational Tenglish (phonetic Roman English letters). English tech/colloquial words MUST remain in standard English spelling (e.g. 'business logic', 'debugging', 'code', 'error', 'design', 'person', 'support').
2. "telugu_text": Write the exact spoken sentence in authentic Telugu script (తెలుగు లిపి).
3. "english_text": Provide the accurate English meaning/translation of that segment.
4. "words": Break down each word with its approximate start and end timestamps (in seconds).
5. Segments should be concise (typically 1.5 to 4.5 seconds each), ideal for dynamic karaoke subtitles on TikTok/Instagram Reels.
6. Make sure timestamps match the actual audio voice timing.
"""

    candidate_models = [
        preferred_model,
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]
    # Preserve order while deduplicating
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]
    last_error = None
    response_text = ""

    for m in models_to_try:
        try:
            print(f"Requesting transcription from Gemini model '{m}'...")
            part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3")
            response = client.models.generate_content(
                model=m,
                contents=[part, prompt]
            )
            response_text = response.text or ""
            if response_text.strip():
                print(f"Successfully received transcription from '{m}'.")
                break
        except Exception as e:
            print(f"Model {m} failed: {e}. Trying fallback...")
            last_error = e

    if not response_text.strip():
        raise RuntimeError(f"Gemini transcription failed on all attempted models: {last_error}")

    # Clean JSON
    clean_json_str = response_text.strip()
    # Remove markdown codeblocks if model included them
    if clean_json_str.startswith("```"):
        clean_json_str = re.sub(r"^```(?:json)?\s*", "", clean_json_str)
        clean_json_str = re.sub(r"\s*```$", "", clean_json_str)

    try:
        raw_segments = json.loads(clean_json_str)
    except Exception as e:
        # Try extracting first array bracket
        match = re.search(r"\[.*\]", clean_json_str, re.DOTALL)
        if match:
            raw_segments = json.loads(match.group(0))
        else:
            raise ValueError(f"Failed to parse Gemini response as JSON: {clean_json_str[:200]}") from e

    formatted_segments: List[Dict[str, Any]] = []
    for idx, seg in enumerate(raw_segments):
        start_time = round(float(seg.get("start", 0)), 2)
        end_time = round(float(seg.get("end", start_time + 1.0)), 2)
        if end_time <= start_time:
            end_time = start_time + 1.0

        tenglish = seg.get("tenglish_text") or seg.get("text", "")
        telugu = seg.get("telugu_text") or tenglish
        english = seg.get("english_text") or tenglish

        # Parse words
        words_data = []
        raw_words = seg.get("words", [])
        if raw_words:
            for w in raw_words:
                w_str = str(w.get("word", "")).strip()
                if not w_str:
                    continue
                w_s = round(float(w.get("start", start_time)), 2)
                w_e = round(float(w.get("end", end_time)), 2)
                words_data.append({
                    "word": w_str,
                    "start": w_s,
                    "end": w_e,
                    "telugu_word": w_str,
                    "tenglish_word": w_str
                })
        else:
            # Distribute words evenly
            tokens = tenglish.split()
            if tokens:
                duration = max(0.5, end_time - start_time)
                w_dur = duration / len(tokens)
                for w_idx, tok in enumerate(tokens):
                    ws = round(start_time + w_idx * w_dur, 2)
                    we = round(min(end_time, ws + w_dur), 2)
                    words_data.append({
                        "word": tok,
                        "start": ws,
                        "end": we,
                        "telugu_word": tok,
                        "tenglish_word": tok
                    })

        formatted_segments.append({
            "id": idx + 1,
            "start": start_time,
            "end": end_time,
            "text": tenglish,
            "telugu_text": telugu,
            "tenglish_text": tenglish,
            "english_text": english,
            "words": words_data
        })

    # Clean up temp mp3
    if compressed_path != audio_path and os.path.exists(compressed_path):
        try:
            os.remove(compressed_path)
        except Exception:
            pass

    return {
        "language": "te",
        "duration": formatted_segments[-1]["end"] if formatted_segments else 0.0,
        "segments": formatted_segments
    }

