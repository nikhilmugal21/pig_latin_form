import streamlit as st
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------
# 1) Basic IPA resources
# ---------------------------

IPA_VOWELS = set("""
i y ɨ ʉ ɯ u ɪ ʏ ʊ e ø ɘ ɵ ɤ o
ə ɚ ɜ ɝ ɞ ɛ œ ɐ ʌ ɔ æ a ɑ ɒ ɶ
""".split())

STRESS_MARKS = {"ˈ", "ˌ"}
SYLLABLE_BREAKS = {".", "·"}

LENGTH_MARKS = {"ː", "ˑ"}
TIE_BARS = {"͡", "͜"}
SYLLABIC_DIACRITIC = "̩"  # U+0329


# ---------------------------
# 2) Data structures
# ---------------------------

@dataclass
class SyllableONC:
    onset: str
    nucleus: str
    coda: str
    stress: Optional[str] = None


# ---------------------------
# 3) IPA tokenization helpers
# ---------------------------

def strip_brackets(ipa: str) -> str:
    ipa = ipa.strip()
    if (ipa.startswith("/") and ipa.endswith("/")) or (ipa.startswith("[") and ipa.endswith("]")):
        ipa = ipa[1:-1].strip()
    return ipa

def is_combining(ch: str) -> bool:
    return unicodedata.category(ch) == "Mn"

def tokenize_ipa(ipa: str) -> List[str]:
    """
    Tokenize IPA into segments:
    - keeps combining diacritics attached to previous base char
    - attaches length marks ː ˑ to previous segment
    - merges tie-bar affricates into one segment: t͡s / t͜s
    - keeps stress marks and syllable breaks as separate tokens
    """
    ipa = strip_brackets(ipa)
    tokens: List[str] = []
    i = 0

    while i < len(ipa):
        ch = ipa[i]

        if ch.isspace():
            i += 1
            continue

        # Keep suprasegmentals and syllable breaks as their own tokens
        if ch in STRESS_MARKS or ch in SYLLABLE_BREAKS:
            tokens.append(ch)
            i += 1
            continue

        # Attach length marks to previous segment
        if ch in LENGTH_MARKS:
            if tokens:
                tokens[-1] += ch
            else:
                tokens.append(ch)
            i += 1
            continue

        # Attach combining marks to previous segment (defensive)
        if is_combining(ch):
            if tokens:
                tokens[-1] += ch
            else:
                tokens.append(ch)
            i += 1
            continue

        # Start a new segment
        seg = ch
        i += 1

        # Attach combining diacritics to this segment
        while i < len(ipa) and is_combining(ipa[i]):
            seg += ipa[i]
            i += 1

        # Attach length marks to this segment
        while i < len(ipa) and ipa[i] in LENGTH_MARKS:
            seg += ipa[i]
            i += 1

        # Tie-bar affricate handling: t + ͡ + s => "t͡s"
        if i < len(ipa) and ipa[i] in TIE_BARS:
            tie = ipa[i]
            i += 1
            if i < len(ipa):
                seg += tie + ipa[i]
                i += 1

                while i < len(ipa) and is_combining(ipa[i]):
                    seg += ipa[i]
                    i += 1

                while i < len(ipa) and ipa[i] in LENGTH_MARKS:
                    seg += ipa[i]
                    i += 1

        tokens.append(seg)

    return tokens


# ---------------------------
# 4) Nucleus detection and vowel merging
# ---------------------------

def base_symbol(seg: str) -> str:
    """
    Heuristic: return the first non-combining character that's not a length/tie mark.
    """
    for ch in seg:
        if not is_combining(ch) and ch not in LENGTH_MARKS and ch not in TIE_BARS:
            return ch
    return seg[:1] if seg else ""

def is_nucleus_segment(seg: str) -> bool:
    """
    Nucleus if:
    - base symbol is a vowel, OR
    - has syllabic diacritic (n̩, l̩, etc.)
    """
    if SYLLABIC_DIACRITIC in seg:
        return True
    return base_symbol(seg) in IPA_VOWELS

def merge_consecutive_vowels(tokens: List[str]) -> List[str]:
    """
    Merge consecutive nucleus-capable segments into one nucleus string:
    - diphthongs/triphthongs become one nucleus segment
    - long vowels already remain single segments because ː attaches at tokenization
    """
    merged: List[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if is_nucleus_segment(t):
            nuc = t
            j = i + 1
            while j < len(tokens) and is_nucleus_segment(tokens[j]):
                nuc += tokens[j]
                j += 1
            merged.append(nuc)
            i = j
        else:
            merged.append(t)
            i += 1
    return merged


# ---------------------------
# 5) Syllables + ONC extraction
# ---------------------------

def split_into_syllables(tokens: List[str]) -> List[List[str]]:
    """
    If '.' or '·' present: split syllables there.
    Otherwise return one syllable with all tokens.
    """
    syllables: List[List[str]] = [[]]
    for t in tokens:
        if t in SYLLABLE_BREAKS:
            if syllables[-1]:
                syllables.append([])
        else:
            syllables[-1].append(t)
    return [s for s in syllables if s]

def onset_nucleus_coda_for_syllable(syl_tokens: List[str]) -> SyllableONC:
    stress = None
    while syl_tokens and syl_tokens[0] in STRESS_MARKS:
        stress = syl_tokens[0]
        syl_tokens = syl_tokens[1:]

    nuc_idx = None
    for i, t in enumerate(syl_tokens):
        if is_nucleus_segment(t):
            nuc_idx = i
            break

    if nuc_idx is None:
        return SyllableONC(onset="".join(syl_tokens), nucleus="", coda="", stress=stress)

    onset = "".join([t for t in syl_tokens[:nuc_idx] if t not in STRESS_MARKS])
    nucleus = syl_tokens[nuc_idx]
    coda = "".join([t for t in syl_tokens[nuc_idx + 1:] if t not in STRESS_MARKS])

    return SyllableONC(onset=onset, nucleus=nucleus, coda=coda, stress=stress)

def segment_word_onc(ipa_word: str) -> List[SyllableONC]:
    tokens = tokenize_ipa(ipa_word)
    syllables = split_into_syllables(tokens)

    results: List[SyllableONC] = []
    for syl in syllables:
        syl_merged = merge_consecutive_vowels(syl)
        results.append(onset_nucleus_coda_for_syllable(syl_merged))
    return results


# ---------------------------
# 6) Pig Latin (IPA-based)
# ---------------------------

def join_syllables_to_ipa(syllables: List[SyllableONC]) -> str:
    return ".".join([s.onset + s.nucleus + s.coda for s in syllables])

def pig_latin_from_ipa(ipa_word: str) -> str:
    """
    Pig Latin via IPA onset of the first syllable:
      - if first onset is empty => vowel-initial => + 'ei'
      - else move that onset cluster to end => + 'ei'
    """
    sylls = segment_word_onc(ipa_word)
    if not sylls:
        return ""

    first = sylls[0]
    original = join_syllables_to_ipa(sylls)

    # fallback if no nucleus
    if first.nucleus == "" and original:
        return original + "ei"

    onset_cluster = first.onset

    if onset_cluster == "":
        return original + "ei"

    rest_first = first.nucleus + first.coda
    rest = ".".join([rest_first] + [s.onset + s.nucleus + s.coda for s in sylls[1:]])
    return rest + onset_cluster + "ei"


# ---------------------------
# 7) Streamlit UI
# ---------------------------

st.set_page_config(page_title="IPA Pig Latin", layout="centered")

st.title("Pig Latin (IPA-based)")

default = "/straɪk/"
ipa_input = st.text_input("IPA input", value=default)


        st.markdown("**Reconstructed IPA**")
        st.code(join_syllables_to_ipa(sylls))

        st.markdown("**Pig Latin (IPA-based)**")
        st.code(piglatin)

