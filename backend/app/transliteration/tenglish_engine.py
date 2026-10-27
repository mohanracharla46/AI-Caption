import re
from typing import List, Dict, Any, Optional
from app.transliteration.english_dict import TELUGU_TO_ENGLISH_WORDS, NATURAL_TELUGU_WORDS

# Telugu Unicode mappings
INDEPENDENT_VOWELS = {
    '\u0C05': 'a',
    '\u0C06': 'aa',
    '\u0C07': 'i',
    '\u0C08': 'ee',
    '\u0C09': 'u',
    '\u0C0A': 'oo',
    '\u0C0B': 'ru',
    '\u0C0C': 'lu',
    '\u0C0E': 'e',
    '\u0C0F': 'e',
    '\u0C10': 'ai',
    '\u0C12': 'o',
    '\u0C13': 'o',
    '\u0C14': 'au'
}

CONSONANTS = {
    '\u0C15': 'k',
    '\u0C16': 'kh',
    '\u0C17': 'g',
    '\u0C18': 'gh',
    '\u0C19': 'ng',
    '\u0C1A': 'ch',
    '\u0C1B': 'chh',
    '\u0C1C': 'j',
    '\u0C1D': 'jh',
    '\u0C1E': 'ny',
    '\u0C1F': 't',
    '\u0C20': 'th',
    '\u0C21': 'd',
    '\u0C22': 'dh',
    '\u0C23': 'n',
    '\u0C24': 'th',
    '\u0C25': 'th',
    '\u0C26': 'd',
    '\u0C27': 'dh',
    '\u0C28': 'n',
    '\u0C2A': 'p',
    '\u0C2B': 'f',
    '\u0C2C': 'b',
    '\u0C2D': 'bh',
    '\u0C2E': 'm',
    '\u0C2F': 'y',
    '\u0C30': 'r',
    '\u0C31': 'r',
    '\u0C32': 'l',
    '\u0C33': 'l',
    '\u0C35': 'v',
    '\u0C36': 'sh',
    '\u0C37': 'sh',
    '\u0C38': 's',
    '\u0C39': 'h'
}

VOWEL_SIGNS = {
    '\u0C3E': 'aa',
    '\u0C3F': 'i',
    '\u0C40': 'ee',
    '\u0C41': 'u',
    '\u0C42': 'oo',
    '\u0C43': 'ru',
    '\u0C44': 'ruu',
    '\u0C46': 'e',
    '\u0C47': 'e',
    '\u0C48': 'ai',
    '\u0C4A': 'o',
    '\u0C4B': 'o',
    '\u0C4C': 'au'
}

VIRAMA = '\u0C4D'    # ్
ANUSVARA = '\u0C02'  # ం
VISARGA = '\u0C03'   # ః
ZWNJ = '\u200C'
ZWJ = '\u200D'

def clean_indic_text(text: str) -> str:
    """Removes invisible formatting characters like ZWNJ and ZWJ."""
    return text.replace(ZWNJ, '').replace(ZWJ, '')

def is_telugu_char(ch: str) -> bool:
    return '\u0C00' <= ch <= '\u0C7F'

def contains_telugu(text: str) -> bool:
    return any(is_telugu_char(ch) for ch in text)

def transliterate_phonetic_word(word: str) -> str:
    """
    Translates a single pure Telugu script word into natural Tenglish.
    Follows conversational phonetics without clumsy academic uppercase letters.
    """
    i = 0
    n = len(word)
    output = []

    while i < n:
        ch = word[i]

        # 1. Independent Vowel
        if ch in INDEPENDENT_VOWELS:
            output.append(INDEPENDENT_VOWELS[ch])
            i += 1
            continue

        # 2. Consonant
        if ch in CONSONANTS:
            cons_sound = CONSONANTS[ch]
            # Check next character
            if i + 1 < n:
                next_ch = word[i + 1]
                if next_ch == VIRAMA:
                    # Halant - suppresses inherent 'a'
                    output.append(cons_sound)
                    i += 2
                    # Note: if followed by another consonant (conjunct), next iteration handles it
                    continue
                elif next_ch in VOWEL_SIGNS:
                    output.append(cons_sound + VOWEL_SIGNS[next_ch])
                    i += 2
                    continue
                elif next_ch == ANUSVARA:
                    # Inherent vowel 'a' + anusvara 'm'
                    # Determine contextually: before d/t -> 'an', before g/k -> 'ang', otherwise 'am'
                    anusvara_sound = 'm'
                    if i + 2 < n:
                        after_next = word[i + 2]
                        if after_next in ['\u0C26', '\u0C27', '\u0C21', '\u0C22', '\u0C24', '\u0C25', '\u0C1F', '\u0C20']:
                            anusvara_sound = 'n'
                        elif after_next in ['\u0C15', '\u0C17']:
                            anusvara_sound = 'ng'
                    output.append(cons_sound + 'a' + anusvara_sound)
                    i += 2
                    continue
                elif next_ch == VISARGA:
                    output.append(cons_sound + 'aha')
                    i += 2
                    continue
                else:
                    # Next is another consonant or normal char - inherent 'a'
                    output.append(cons_sound + 'a')
                    i += 1
                    continue
            else:
                # Word-ending consonant without virama has inherent vowel 'a'
                # e.g. కొత్త -> kottha, పెద్ద -> pedda, అమ్మ -> amma
                output.append(cons_sound + 'a')
                i += 1
                continue

        # 3. Standalone Anusvara
        if ch == ANUSVARA:
            # Contextual anusvara
            anusvara_sound = 'm'
            if i + 1 < n and word[i + 1] in ['\u0C26', '\u0C27', '\u0C21', '\u0C22', '\u0C24', '\u0C25', '\u0C1F', '\u0C20']:
                anusvara_sound = 'n'
            output.append(anusvara_sound)
            i += 1
            continue

        # 4. Standalone Visarga
        if ch == VISARGA:
            output.append('h')
            i += 1
            continue

        # 5. Non-Telugu or unrecognized
        output.append(ch)
        i += 1

    result = "".join(output)

    # Post-cleanups for natural readability
    # Drop trailing awkward 'a' if word ends with common suffixes like 'mu' -> 'm'
    result = re.sub(r'([bcdfghjklmnpqrstvwxyz])amu$', r'\1am', result)
    result = re.sub(r'([bcdfghjklmnpqrstvwxyz])amu\b', r'\1am', result)
    
    # Fix awkward spellings like "thth" -> "tth" or "tt", "chch" -> "cch"
    result = result.replace("thth", "tth").replace("chch", "cch")
    result = result.replace("shsh", "ssh").replace("khkh", "kkh")
    
    return result

# Common Whisper phonetic acoustic spellings to canonical Tenglish & English
ACOUSTIC_VARIANTS = {
    "paitan": "Python",
    "paithan": "Python",
    "pythan": "Python",
    "mariu": "mariyu",
    "kotha": "kottha",
    "ipudu": "ippudu",
    "neerchukundam": "nerchukundam",
    "chedaam": "cheddam",
    "cheddaam": "cheddam",
    "frens": "friends",
    "frends": "friends"
}

def transliterate_token(token: str) -> str:
    """
    Transliterates a single token (which could be a word with punctuation,
    English word, Telugu word, number, etc.)
    """
    if not token:
        return token
    token = clean_indic_text(token)

    # Extract leading and trailing punctuation
    match = re.match(r"^([^\w\u0C00-\u0C7F]*)([\w\u0C00-\u0C7F]+)([^\w\u0C00-\u0C7F]*)$", token)
    if not match:
        if not contains_telugu(token):
            return ACOUSTIC_VARIANTS.get(token.lower(), token)
        return transliterate_phonetic_word(token)

    prefix, core_word, suffix = match.groups()

    # If it's already Latin/Roman letters, check acoustic variants (e.g. paitan -> Python)
    if not contains_telugu(core_word):
        lower_core = core_word.lower()
        if lower_core in ACOUSTIC_VARIANTS:
            replacement = ACOUSTIC_VARIANTS[lower_core]
            # Match capitalization if original was capitalized
            if core_word[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            return f"{prefix}{replacement}{suffix}"
        return token

    # 1. Exact match in Telugu-to-English loanword/tech dictionary
    if core_word in TELUGU_TO_ENGLISH_WORDS:
        translated = TELUGU_TO_ENGLISH_WORDS[core_word]
        return f"{prefix}{translated}{suffix}"

    # 2. Exact match in natural Telugu colloquial dictionary
    if core_word in NATURAL_TELUGU_WORDS:
        natural_word = NATURAL_TELUGU_WORDS[core_word]
        return f"{prefix}{natural_word}{suffix}"

    # 3. Check lowercase / cleaned
    cleaned_core = core_word.strip()
    if cleaned_core in TELUGU_TO_ENGLISH_WORDS:
        return f"{prefix}{TELUGU_TO_ENGLISH_WORDS[cleaned_core]}{suffix}"

    # 4. Phonetic transliteration
    phonetic = transliterate_phonetic_word(core_word)
    return f"{prefix}{phonetic}{suffix}"

def to_tenglish(text: str) -> str:
    """
    Converts a full sentence or paragraph of Telugu/mixed text into natural Tenglish.
    Preserves English words, numbers, and punctuation.
    Capitalizes the beginning of sentences nicely.
    """
    if not text:
        return ""

    tokens = re.split(r'(\s+)', text)
    result_tokens = []

    for tok in tokens:
        if not tok or tok.isspace():
            result_tokens.append(tok)
        else:
            result_tokens.append(transliterate_token(tok))

    result = "".join(result_tokens)

    # Format sentence casing: Capitalize first letter of each sentence
    def capitalize_sentence(m):
        prefix = m.group(1) or ""
        first_char = m.group(2)
        rest = m.group(3) or ""
        return f"{prefix}{first_char.upper()}{rest}"

    # Capitalize start of text
    result = re.sub(r'^(\s*)([a-z])(.*)$', capitalize_sentence, result, flags=re.DOTALL)
    # Capitalize after period, question mark, or exclamation
    result = re.sub(r'([.?!]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)

    return result

def convert_segments(segments: List[Dict[str, Any]], mode: str = "tenglish") -> List[Dict[str, Any]]:
    """
    Converts an array of subtitle segments (each with start, end, text, words)
    into the selected mode ('tenglish', 'telugu', or 'english').
    """
    converted = []
    for seg in segments:
        new_seg = dict(seg)
        telugu_text = seg.get("telugu_text") or seg.get("text", "")
        english_text = seg.get("english_text", "")

        # Always store the original telugu_text for switching modes later
        new_seg["telugu_text"] = telugu_text
        tenglish_text = seg.get("tenglish_text") or to_tenglish(telugu_text)
        new_seg["tenglish_text"] = tenglish_text

        # Active display text based on mode
        if mode == "telugu":
            new_seg["text"] = telugu_text
        elif mode == "english" and english_text:
            new_seg["text"] = english_text
        else:
            new_seg["text"] = tenglish_text

        # Transliterate word-level timestamps if present
        if "words" in seg and isinstance(seg["words"], list):
            new_words = []
            for w in seg["words"]:
                word_copy = dict(w)
                w_telugu = word_copy.get("telugu_word") or word_copy.get("word", "")
                word_copy["telugu_word"] = w_telugu
                w_tenglish = word_copy.get("tenglish_word") or transliterate_token(w_telugu)
                word_copy["tenglish_word"] = w_tenglish

                if mode == "telugu":
                    word_copy["word"] = w_telugu
                elif mode == "english" and word_copy.get("english_word"):
                    word_copy["word"] = word_copy["english_word"]
                else:
                    word_copy["word"] = w_tenglish

                new_words.append(word_copy)
            new_seg["words"] = new_words

        converted.append(new_seg)

    return converted
