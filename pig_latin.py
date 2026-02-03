import streamlit as st
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------
# IPA resources
# ---------------------------

IPA_VOWELS = set("""
i y ɨ ʉ ɯ u ɪ ʏ ʊ e ø ɘ ɵ ɤ o
ə ɚ ɜ ɝ ɞ ɛ œ ɐ ʌ ɔ æ a ɑ ɒ ɶ
""".split())

STRESS_MARKS = {"ˈ", "ˌ"}
SYLLABLE_BREAKS = {".", "·"}
LENGTH_MARKS = {"ː", "ˑ"}
TIE_BARS = {"͡", "͜"}
SYLLABIC_DIACRITIC = "̩"


# ---------------------------
# Data structure
# ---------------------------

@dataclass
class SyllableONC:
    onset: str
    nucleus: str
    coda: str
    stress: Optional[str] = None


# ---------------------------
# IPA processing
# ---------------------------

def strip_brackets(ipa: str) -> str:
    ipa = ipa.strip()
    if (ipa.startswith("/") and ipa.endswith("/")) or (ipa.startswith("[") and ipa.endswith("]")):
        ipa = ipa[1:-1].strip()
    return ipa

def is_combining(ch: str) -> bool:
    return unicodedata.category(ch) == "Mn"

def tokenize_ipa(ipa: str) -> List[str]:
    ipa = strip_brackets(ipa)
    tokens = []
    i = 0

    while i < len(ipa):
        ch = ipa[i]

        if ch.isspace():
            i += 1
            continue

        if ch in STRESS_MARKS or ch in SYLLABLE_BREAKS:
            tokens.append(ch)
            i += 1
            continue

        if ch in LENGTH_MARKS:
            if tokens:
                tokens[-1] += ch
            i += 1
            continue

        if is_combining(ch):
            if tokens:
                tokens[-1] += ch
            i += 1
            continue

        seg = ch
        i += 1

        while i < len(ipa) and is_combining(ipa[i]):
            seg += ipa[i]
            i += 1

        while i < len(ipa) and ipa[i] in LENGTH_MARKS:
            seg += ipa[i]
            i += 1

        if i < len(ipa) and ipa[i] in TIE_BARS:
            tie = ipa[i]
            i += 1
            if i < len(ipa):
                seg += tie + ipa[i]
                i += 1
                while i < len(ipa) and is_combining(ipa[i]):
                    seg += ipa[i]
                    i += 1

        tokens.append(seg)

    return tokens


def base_symbol(seg: str) -> str:
    for ch in seg:
        if not is_combining(ch) and ch not in LENGTH_MARKS and ch not in TIE_BARS:
            return ch
    return seg[:1]

def is_nucleus_segment(seg: str) -> bool:
    return SYLLABIC_DIACRITIC in seg or base_symbol(seg) in IPA_VOWELS

def merge_consecutive_vowels(tokens: List[str]) -> List[str]:
    merged = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if is_nucleus_segment(t):
            nucleus = t
            j = i + 1
            while j < len(tokens) and is_nucleus_segment(tokens[j]):
                nucleus += tokens[j]
                j += 1
            merged.append(nucleus)
            i = j
        else:
            merged.append(t)
            i += 1
    return merged


def split_into_syllables(tokens: List[str]) -> List[List[str]]:
    syllables = [[]]
    for t in tokens:
        if t in SYLLABLE_BREAKS:
            if syllables[-1]:
                syllables.append([])
        else:
            syllables[-1].append(t)
    return [s for s in syllables if s]


def onset_nucleus_coda_for_syllable(syl_tokens: List[str]) -> SyllableONC:
    while syl_tokens and syl_tokens[0] in STRESS_MARKS:
        syl_tokens = syl_tokens[1:]

    for i, t in enumerate(syl_tokens):
        if is_nucleus_segment(t):
            return SyllableONC(
                onset="".join(syl_tokens[:i]),
                nucleus=t,
                coda="".join(syl_tokens[i + 1 :])
            )

    return SyllableONC(onset="".join(syl_tokens), nucleus="", coda="")


def segment_word_onc(ipa_word: str) -> List[SyllableONC]:
    tokens = tokenize_ipa(ipa_word)
    syllables = split_into_syllables(tokens)

    return [
        onset_nucleus_coda_for_syllable(merge_consecutive_vowels(s))
        for s in syllables
    ]


# ---------------------------
# Pig Latin
# ---------------------------

def join_syllables(sylls: List[SyllableONC]) -> str:
    return ".".join(s.onset + s.nucleus + s.coda for s in sylls)

def pig_latin_from_ipa(ipa_word: str) -> str:
    sylls = segment_word_onc(ipa_word)
    if not sylls:
        return ""

    first = sylls[0]
    original = join_syllables(sylls)

    if first.onset == "":
        return original + "ei"

    rest_first = first.nucleus + first.coda
    rest = ".".join([rest_first] + [s.onset + s.nucleus + s.coda for s in sylls[1:]])

    return rest + first.onset + "ei"


# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="IPA Pig Latin", layout="centered")
st.title("IPA → Pig Latin")

ipa_input = st.text_input("Enter an IPA word", value="/straɪk/")

if ipa_input.strip():
    piglatin = pig_latin_from_ipa(ipa_input)
    st.subheader("Pig Latin (IPA-based)")
    st.code(piglatin)
