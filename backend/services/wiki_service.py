# filename: backend/services/wiki_service.py
from __future__ import annotations

import httpx
from typing import Optional, Dict, Any, List
import re

WIKI_API = "https://en.wikipedia.org/w/api.php"

# Required to avoid 403 blocks
WIKI_HEADERS = {
    "User-Agent": "GamingChatbot/1.0 (https://github.com/byrnai0/gaming-chatbot-2.0)"
}


class WikiService:
    """Wikipedia fetch + section extraction + cleaning."""

    async def fetch_wiki_page_raw(self, title: str) -> Optional[str]:
        """
        Fetch the full plain-text extract of a Wikipedia page.
        Returns None if not found.
        """
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "format": "json",
            "titles": title,
            "redirects": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0, headers=WIKI_HEADERS) as client:
                resp = await client.get(WIKI_API, params=params)
                resp.raise_for_status()
                data = resp.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None

            # Extract the page text
            for _, page in pages.items():
                if "extract" in page and page["extract"]:
                    return page["extract"]

            return None

        except Exception:
            return None

    def extract_section(self, raw_text: str, section: str) -> Optional[str]:
        """
        Extract a section (e.g., "Plot", "Characters", "Gameplay", "Development") from raw wiki text.
        Uses a simple heading-based split approach.
        """
        if not raw_text:
            return None

        # Normalize for matching
        section = section.lower().strip()

        # Split by headings
        parts = re.split(r"\n==+\s*(.+?)\s*==+\n", raw_text)

        # parts = [before first heading, heading1, text1, heading2, text2, ...]
        for i in range(1, len(parts), 2):
            heading = parts[i].lower()
            body = parts[i + 1]

            if section in heading:
                # Stop at next subheading to avoid leakage of unrelated sections
                body = re.split(r"\n==+", body)[0]
                return body.strip()

        return None

    def clean_wiki_text(self, text: str) -> str:
        """
        Remove references like [1], [2], [citation needed], and excessive whitespace.
        """
        if not text:
            return ""

        # Remove [1], [23], etc.
        cleaned = re.sub(r"\[\d+\]", "", text)

        # Remove [citation needed] and similar
        cleaned = re.sub(r"\[citation needed\]", "", cleaned, flags=re.IGNORECASE)

        # Normalize whitespace
        cleaned = re.sub(r"\s+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
        cleaned = cleaned.strip()

        return cleaned
