# IPA ONC Segmenter + Pig Latin (Streamlit)

This project is a **Streamlit-based linguistic tool** that works directly with **IPA (International Phonetic Alphabet)** input.  
It segments words into **onset, nucleus, and coda** and generates **Pig Latin** using **phonological (IPA-based) rules** rather than spelling-based heuristics.

The app is intended for students, researchers, and NLP practitioners interested in **phonology, syllable structure, and IPA processing**.

---

## Features

- IPA tokenization with support for:
  - Combining diacritics
  - Length marks (`ː`, `ˑ`)
  - Affricates with tie bars (`t͡s`, `t͜ʃ`)
- Onset–Nucleus–Coda (ONC) segmentation
- Treats:
  - **Monophthongs**
  - **Diphthongs / vowel sequences**
  - **Long vowels**
  as a **single nucleus**
- Supports **syllabic consonants** (e.g. `n̩`, `l̩`)
- Multi-syllable analysis when syllable breaks (`.` or `·`) are provided
- **IPA-based Pig Latin generation**:
  - Vowel-initial → `+ei`
  - Consonant-initial → move first syllable onset → `+ei`
- Interactive **Streamlit UI**

---

## Example

Input:/kəmpjuːtər/
Output: /əmpjuːtərkei/

