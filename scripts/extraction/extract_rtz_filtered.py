#!/usr/bin/env python3
import sys
import re
import json
import requests
from pathlib import Path
from dataclasses import dataclass
import unicodedata

# Text cleaning patterns
CLEANER_KANA = re.compile(r'<\|([^|]+)\|[^|]*\|>')
CLEANER_TAGS = re.compile(r'\{\$\d+\}|\{\$\}')

@dataclass
class Segment:
    prefix_pos: int
    content_start: int
    content_end: int
    raw: str
    clean: str
    translation: str = ""
    is_valid: bool = False

def is_japanese_text(text: str) -> bool:
    """Check if text contains meaningful Japanese characters"""
    if not text or len(text.strip()) < 3:
        return False
    
    # Remove whitespace and basic punctuation
    clean_text = re.sub(r'[\s\.,!?\-・。、†\n\r]+', '', text)
    if len(clean_text) < 3:
        return False
    
    japanese_chars = 0
    total_chars = 0
    
    for char in clean_text:
        if char.isprintable():
            total_chars += 1
            # Check for Japanese character ranges
            if (
                '\u3040' <= char <= '\u309F' or  # Hiragana
                '\u30A0' <= char <= '\u30FF' or  # Katakana
                '\u4E00' <= char <= '\u9FAF' or  # CJK Unified Ideographs
                '\uFF00' <= char <= '\uFFEF'     # Halfwidth/Fullwidth Forms
            ):
                japanese_chars += 1
    
    if total_chars == 0:
        return False
    
    # Text should be at least 30% Japanese characters
    japanese_ratio = japanese_chars / total_chars
    return japanese_ratio >= 0.3

def contains_game_terms(text: str) -> bool:
    """Check for Vanguard-specific terms"""
    game_terms = [
        'ヴァンガード', 'vanguard', 'ガード', 'guard',
        'アタック', 'attack', 'ダメージ', 'damage', 
        'ブースト', 'boost', 'パワー', 'power',
        'リアガード', 'rear', 'ドライブ', 'drive',
        'チェック', 'check', 'トリガー', 'trigger',
        'ユニット', 'unit', 'カード', 'card',
        'バトル', 'battle', 'ターン', 'turn',
        'フィールド', 'field', 'ステップ', 'step'
    ]
    
    text_lower = text.lower()
    return any(term in text_lower for term in game_terms)

def has_dialogue_patterns(text: str) -> bool:
    """Check for dialogue/tutorial patterns"""
    dialogue_patterns = [
        r'[。！？]',  # Japanese sentence endings
        r'だよ|です|である|だね|でしょ|わ。|の。|よ。',  # Japanese sentence endings
        r'これ|それ|あれ|この|その|あの',  # Japanese demonstratives
        r'です|ます|だ|である',  # Japanese copula/verb endings
        r'[って|という|といった]',  # Japanese quotation patterns
    ]
    
    return any(re.search(pattern, text) for pattern in dialogue_patterns)

def is_likely_filepath_or_junk(text: str) -> bool:
    """Check if text looks like file paths or binary junk"""
    junk_patterns = [
        r'^[a-zA-Z]:[/\\]',  # Windows paths
        r'/[a-zA-Z0-9_]+/',  # Unix paths
        r'\.(?:dll|exe|bin|rtz|orb)$',  # File extensions
        r'^[0-9A-Fa-f]{8,}$',  # Long hex strings
        r'^Copyright.*All Rights Reserved',  # Copyright notices
        r'楲瑰|潴た|畴潴|瑥畴',  # Garbled text patterns from your output
        r'^[^\u3040-\u9FAF\uFF00-\uFFEF\w\s]{5,}',  # Long strings without readable chars
    ]
    
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in junk_patterns)

def clean_text(s: str) -> str:
    """Clean Japanese text while preserving meaning"""
    # 1) Convert <|漢字|読み|> → 漢字
    s = CLEANER_KANA.sub(r'\1', s)
    # 2) Remove {$123456} tags
    s = CLEANER_TAGS.sub('', s)
    # 3) Normalize whitespace but preserve newlines
    s = re.sub(r'[ \t]+', ' ', s)
    # 4) Convert † back to newlines
    s = s.replace('†', '\n')
    return s.strip()

def translate(text: str) -> str:
    """Translate text using LibreTranslate"""
    try:
        # Preserve newline positions
        line_positions = []
        total_len = len(text)
        for i, ch in enumerate(text):
            if ch == "\n":
                line_positions.append(i / total_len)
        
        # Translate on single line
        single_line = text.replace("\n", " ")
        
        resp = requests.post(
            "http://localhost:5001/translate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "q": single_line,
                "source": "ja", 
                "target": "en",
                "format": "text"
            }),
            timeout=10
        )
        resp.raise_for_status()
        translated = resp.json().get("translatedText", "")
        
        # Reinsert newlines approximately
        if line_positions and translated:
            chars = list(translated)
            for pct in line_positions:
                pos = int(pct * len(chars))
                # Move back to space or start
                while pos > 0 and chars[pos] not in (" ", "-", "\u2014"):
                    pos -= 1
                if pos > 0:
                    chars[pos] = "\n"
            translated = "".join(chars)
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def extract_segments(data: bytes, start_offset: int) -> list[Segment]:
    """Extract text segments from RTZ data"""
    pos = start_offset
    segments: list[Segment] = []
    idx = 1
    
    print("== Extracting segments ==")
    
    while pos + 5 <= len(data):
        # Stop on terminator
        if data[pos:pos+5] == b'\xFF\xFF\xFF\xFF\x00':
            print(f"Reached terminator at 0x{pos:X}, stopping.\n")
            break

        L = data[pos+4]  # Number of UTF-16 units
        byte_len = L * 2
        cs, ce = pos+5, pos+5+byte_len
        
        if ce > len(data):
            print(f"⚠ Segment [{idx}] out of bounds, aborting.\n")
            break

        try:
            raw_bytes = data[cs:ce]
            raw_str = raw_bytes.decode("utf-16-le", errors="ignore")
            clean = clean_text(raw_str)
            
            # Filter criteria
            is_valid = (
                len(clean.strip()) >= 3 and
                not is_likely_filepath_or_junk(clean) and
                (is_japanese_text(clean) or 
                 contains_game_terms(clean) or 
                 has_dialogue_patterns(clean))
            )
            
            # Only print valid segments to reduce noise
            if is_valid:
                print(f"[{idx}] VALID - prefix@0x{pos:X}: L={L} → {byte_len} bytes")
                print(f"    → CLEAN: {repr(clean)}\n")
            
            segments.append(Segment(pos, cs, ce, raw_str, clean, is_valid=is_valid))
            
        except Exception as e:
            print(f"[{idx}] ERROR processing segment: {e}")
            segments.append(Segment(pos, cs, ce, "", "", is_valid=False))
        
        pos = ce
        idx += 1

    valid_count = sum(1 for s in segments if s.is_valid)
    print(f"Total segments extracted: {len(segments)}")
    print(f"Valid Japanese segments: {valid_count}\n")
    return segments

def extract_only(input_file: str, start_offset: int):
    """Extract text without translation for analysis"""
    data = Path(input_file).read_bytes()
    segments = extract_segments(data, start_offset)
    
    print("== Valid Japanese Text Segments ==")
    valid_segments = [s for s in segments if s.is_valid]
    
    for i, seg in enumerate(valid_segments, 1):
        print(f"[{i}] {repr(seg.clean)}")
    
    return valid_segments

def translate_and_patch(input_file: str, start_offset: int):
    """Full extraction, translation, and patching"""
    buf = bytearray(Path(input_file).read_bytes())
    segments = extract_segments(buf, start_offset)
    
    valid_segments = [s for s in segments if s.is_valid]
    print(f"== Translating {len(valid_segments)} valid segments ==")
    
    for i, seg in enumerate(valid_segments, 1):
        seg.translation = translate(seg.clean)
        print(f"[{i}] JAPANESE:  '{seg.clean}'")
        print(f"    → ENGLISH:  '{seg.translation}'\n")

    print("== Patching file (valid segments only) ==")
    for seg in reversed(segments):
        if not seg.is_valid:
            continue
            
        orig_len = seg.content_end - seg.content_start
        new_raw = seg.translation.encode("utf-16-le")
        
        # Pad or truncate to fit
        if len(new_raw) < orig_len:
            pad = (orig_len - len(new_raw)) // 2
            new_raw += b"\x20\x00" * pad
        else:
            new_raw = new_raw[:orig_len]
        
        # Update length byte
        new_units = len(new_raw) // 2
        buf[seg.prefix_pos + 4] = new_units & 0xFF
        
        # Replace content
        buf[seg.content_start:seg.content_end] = new_raw

    out_path = Path(input_file).with_name(Path(input_file).stem + "_translated")
    Path(out_path).write_bytes(buf)
    print(f"✔ Translated file written to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_rtz_filtered.py <input> <start_offset> [translate]")
        print("  Without 'translate': Extract and show valid text only")
        print("  With 'translate': Extract, translate, and patch file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    start_offset = int(sys.argv[2], 0)
    do_translate = len(sys.argv) > 3 and sys.argv[3].lower() == 'translate'
    
    if do_translate:
        translate_and_patch(input_file, start_offset)
    else:
        extract_only(input_file, start_offset)