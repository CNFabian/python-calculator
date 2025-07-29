#!/usr/bin/env python3
"""
Fix Vanguard term replacement in translation pipeline
The issue is that we need to replace terms in the translated English text, not the Japanese
"""
import re

# Expanded Vanguard terms mapping
VANGUARD_TERMS = {
    # Japanese -> English (for reference)
    "ヴァンガード": "Vanguard",
    "リアガード": "Rear-guard", 
    "ダメージ": "Damage",
    "アタック": "Attack",
    "ガード": "Guard",
    "ドライブチェック": "Drive Check",
    "トリガー": "Trigger",
    "ファイト": "Fight",
    "デッキ": "Deck",
    "ソウル": "Soul",
    "ドロップゾーン": "Drop Zone",
    "ダメージゾーン": "Damage Zone",
    "ガーディアン": "Guardian",
    "インターセプト": "Intercept",
    "ブースト": "Boost",
    "ライド": "Ride",
    "コール": "Call",
    "スタンド": "Stand",
    "レスト": "Rest",
    "パワー": "Power",
    "クリティカル": "Critical",
    "シールド": "Shield",
    "グレード": "Grade",
    "ユニット": "Unit",
    "クラン": "Clan",
    "カード": "Card",
    "フィールド": "Field",
    "サークル": "Circle",
    "ターン": "Turn",
    "フェイズ": "Phase"
}

# English term corrections (what LibreTranslate might produce -> what we want)
ENGLISH_CORRECTIONS = {
    # Common LibreTranslate mistakes for Vanguard terms
    "vanguard": "Vanguard",
    "rear guard": "Rear-guard",
    "rear-guard": "Rear-guard",
    "damage": "Damage",
    "attack": "Attack", 
    "guard": "Guard",
    "drive check": "Drive Check",
    "Drive check": "Drive Check",
    "trigger": "Trigger",
    "fight": "Fight",
    "deck": "Deck",
    "soul": "Soul",
    "drop zone": "Drop Zone",
    "damage zone": "Damage Zone",
    "guardian": "Guardian",
    "intercept": "Intercept",
    "boost": "Boost",
    "ride": "Ride",
    "call": "Call",
    "stand": "Stand",
    "rest": "Rest",
    "power": "Power",
    "critical": "Critical",
    "shield": "Shield",
    "grade": "Grade",
    "unit": "Unit",
    "clan": "Clan",
    "card": "Card",
    "field": "Field",
    "circle": "Circle",
    "turn": "Turn",
    "phase": "Phase"
}

def apply_vanguard_terminology(translated_text: str) -> str:
    """
    Apply Vanguard-specific terminology to translated English text
    This fixes common LibreTranslate mistakes and ensures proper capitalization
    """
    if not translated_text:
        return translated_text
    
    # Apply English corrections (case-insensitive)
    for wrong_term, correct_term in ENGLISH_CORRECTIONS.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(wrong_term) + r'\b'
        translated_text = re.sub(pattern, correct_term, translated_text, flags=re.IGNORECASE)
    
    # Clean up common issues
    translated_text = translated_text.replace('。', '.')  # Japanese period -> English period
    translated_text = re.sub(r'\s+', ' ', translated_text)  # Multiple spaces -> single space
    translated_text = translated_text.strip()
    
    return translated_text

def test_term_replacement():
    """Test the improved term replacement"""
    test_cases = [
        "Learn the basic rules of vanguard。",
        "Attack and damage",
        "Drive check。", 
        "Select the card you want to guard。"
    ]
    
    print("🧪 Testing improved Vanguard term replacement:")
    print("-" * 50)
    
    for i, test_text in enumerate(test_cases, 1):
        corrected = apply_vanguard_terminology(test_text)
        print(f"[{i}] Original: {test_text}")
        print(f"    Fixed:    {corrected}")
        print()

if __name__ == "__main__":
    test_term_replacement()