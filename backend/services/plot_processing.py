#plot processing utilities for spoiler handling and text cleaning
from __future__ import annotations
import re
from typing import Tuple


#Check if user input indicates spoiler intent
SPOILER_KEYWORDS = [
    "spoiler", "spoil", "ending", "end of", "plot twist", "who dies", "death of",
    "reveal", "true ending", "bad ending", "good ending", "secret ending",
]

def detect_spoiler_intent(user_input: str) -> bool:
    """Return True if user input suggests they want spoilers."""
    text = user_input.lower()
    return any(word in text for word in SPOILER_KEYWORDS)


#Remove any unwanted text element from plot summaries
def clean_plot_text(text: str) -> str:
    """Normalize plot text before further processing."""
    text = re.sub(r"\[\d+\]", "", text)          # Remove [1], [2], etc
    text = re.sub(r"\s{2,}", " ", text)          # Remove double spaces
    text = re.sub(r"\([^)]{0,30}\)", "", text)   # Remove small bracketed notes 
    return text.strip()


#Split plot text into early, mid, late sections
def split_plot_sections(text: str) -> Tuple[str, str, str]:
    """
    Very rough segmentation: first 30% = early (safe), next 40% = mid (partial),
    final 30% = late (spoilers).
    Returns (early, mid, late).
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) < 4:
        return text, "", ""

    n = len(sentences)
    early = sentences[: max(1, n // 3)]
    mid = sentences[n // 3 : (2 * n) // 3]
    late = sentences[(2 * n) // 3 :]

    return (
        " ".join(early).strip(),
        " ".join(mid).strip(),
        " ".join(late).strip(),
    )


#Spoiler free extraction for NS-Medium
def extract_spoiler_free(text: str) -> str:
    """
    Keep only early premise + partial setup. Remove mid-game twists + ending.
    """
    text = clean_plot_text(text)
    early, mid, _late = split_plot_sections(text)

    # Keep early, and optionally some non-twist mid sentences.
    # Remove twist markers from mid.
    safe_mid_sentences = []
    twist_markers = ["betray", "twist", "reveals", "secret", "dies", "death", "kills", "final", "ending", "confronts"]

    for sentence in mid.split("."):
        s = sentence.strip().lower()
        if not s:
            continue
        if any(word in s for word in twist_markers):
            continue  # remove spoilers
        safe_mid_sentences.append(sentence.strip())

    safe_mid = ". ".join(safe_mid_sentences[:2]).strip()

    final_text = early
    if safe_mid:
        final_text += " " + safe_mid

    return final_text.strip()


#Full spoiler extraction
def extract_full_spoilers(text: str) -> str:
    """Return cleaned full plot text (no trimming)."""
    return clean_plot_text(text)


#Condense plot into short summary
def condense_plot(text: str, max_sentences: int = 5) -> str:
    """
    Compress a plot into a short readable summary.
    Useful for 'summary' or TL;DR output.
    """
    text = clean_plot_text(text)
    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) <= max_sentences:
        return text
    return " ".join(sentences[:max_sentences]).strip()
