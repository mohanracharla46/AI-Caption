from typing import List, Dict, Any, Optional

def hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
    """
    Converts '#RRGGBB' to ASS color format '&HAABBGGRR'.
    alpha: 0 = fully opaque, 255 = fully transparent in ASS.
    """
    hex_clean = hex_str.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join(c * 2 for c in hex_clean)
    if len(hex_clean) >= 6:
        r = hex_clean[0:2]
        g = hex_clean[2:4]
        b = hex_clean[4:6]
    else:
        r, g, b = "FF", "FF", "FF"

    alpha_hex = f"{alpha:02X}"
    return f"&H{alpha_hex}{b}{g}{r}"

def format_ass_time(seconds: float) -> str:
    """Converts seconds into ASS timestamp format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def generate_ass_subtitles(
    segments: List[Dict[str, Any]],
    style: Optional[Dict[str, Any]] = None,
    video_width: int = 1280,
    video_height: int = 720
) -> str:
    """
    Generates an ASS format subtitle script with custom styling and optional
    word-level Reels highlight.
    """
    if style is None:
        style = {}

    font_name = style.get("font_name", "Arial")
    font_size = int(style.get("font_size", 24))
    primary_color = hex_to_ass_color(style.get("primary_color", "#FFFFFF"), 0)
    highlight_color = hex_to_ass_color(style.get("highlight_color", "#A855F7"), 0)
    outline_color = hex_to_ass_color(style.get("outline_color", "#000000"), 0)
    bg_color = hex_to_ass_color(style.get("background_color", "#000000"), int(style.get("background_alpha", 128)))
    outline_width = float(style.get("outline_width", 2.0))
    shadow_offset = float(style.get("shadow_offset", 1.0))
    
    # Alignment: 2 = bottom center, 5 = middle center (reels), 8 = top center
    position = style.get("position", "bottom")
    alignment = 2
    margin_v = int(style.get("margin_v", 40))
    if position == "middle" or position == "center":
        alignment = 5
        margin_v = 0
    elif position == "top":
        alignment = 8

    # Border style: 1 = outline + drop shadow, 3 = opaque box
    border_style = 3 if style.get("box_background", False) else 1
    is_reels = style.get("is_reels", False)

    header = f"""[Script Info]
Title: Tenglish Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},{highlight_color},{outline_color},{bg_color},-1,0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_offset},{alignment},20,20,{margin_v},1
Style: Highlight,{font_name},{font_size},{highlight_color},{primary_color},{outline_color},{bg_color},-1,0,0,0,105,105,0,0,{border_style},{outline_width},{shadow_offset},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start_sec = float(seg.get("start", 0))
        end_sec = float(seg.get("end", 0))
        words = seg.get("words", [])

        # If Reels mode with word timestamps, create micro-dialogue lines highlighting the active word
        if is_reels and words and len(words) > 1:
            for w_idx, w in enumerate(words):
                w_start = float(w.get("start", start_sec))
                w_end = float(w.get("end", end_sec))
                if w_end <= w_start:
                    w_end = w_start + 0.3

                # Build line with current word highlighted in highlight_color
                line_words = []
                for j, other_w in enumerate(words):
                    w_text = other_w.get("word", "").strip()
                    if j == w_idx:
                        # Highlighted word with ASS color override and subtle scale
                        line_words.append(f"{{\\c{highlight_color}\\b1\\fscx108\\fscy108}}{w_text}{{\\r}}")
                    else:
                        line_words.append(w_text)

                styled_text = " ".join(line_words)
                events.append(
                    f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{styled_text}"
                )
        else:
            # Standard sentence subtitle
            events.append(
                f"Dialogue: 0,{format_ass_time(start_sec)},{format_ass_time(end_sec)},Default,,0,0,0,,{text}"
            )

    return header + "\n".join(events) + "\n"
