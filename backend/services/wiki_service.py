# filename: backend/services/wiki_service.py
# Stage 2 – W3 Hybrid Setup (Wiki API version, silent, modular, flexible section matching)

from __future__ import annotations
import httpx
from typing import Optional, Dict, List


class WikiService:
    """
    Wikipedia data fetcher for gaming chatbot – API version (no scraping).
    W-Auto: Smart title search
    S-Flexible: Can extract sections like Plot, Story, Synopsis, Characters, Development, etc.
    Returns plain text only. No spoilers here – Stage 3 will handle that.
    """

    BASE_API = "https://en.wikipedia.org/w/api.php"

    # Flexible synonyms for sections
    _SECTION_SYNONYMS: Dict[str, List[str]] = {
        "plot": ["plot", "story", "synopsis", "plot summary", "storyline"],
        "characters": ["characters", "cast", "main characters", "playable characters"],
        "development": ["development", "production", "creation"],
        "gameplay": ["gameplay", "mechanics", "game play"],
    }

    async def _search_title(self, title: str) -> Optional[str]:
        """Auto-search Wikipedia page title (W-Auto). Returns best matching page title or None."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": title,
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(self.BASE_API, params=params)
            r.raise_for_status()
            data = r.json()

        hits = data.get("query", {}).get("search", [])
        if not hits:
            return None

        # First hit → best match
        return hits[0].get("title")

    async def fetch_wiki_page_raw(self, title: str) -> Optional[str]:
        """
        Fetch the FULL raw extract of a Wikipedia page as plain text.
        Uses smart search first, then fetches.
        Returns raw text or None.
        """
        page_title = await self._search_title(title)
        if not page_title:
            return None

        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "titles": page_title,
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(self.BASE_API, params=params)
            r.raise_for_status()
            data = r.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page = next(iter(pages.values()))
        return page.get("extract") or None

    def clean_wiki_text(self, text: str) -> str:
        """
        Remove citation markers like [1], [23], etc + extra whitespace.
        Does not remove spoilers (Stage 3).
        """
        import re
        text = re.sub(r"\[\d+\]", "", text)              # Remove [1], [2], etc
        text = re.sub(r"\s{2,}", " ", text)              # Collapse multiple spaces
        text = text.replace("()", "").strip()
        return text

    def extract_section(self, raw_text: str, section_name: str) -> Optional[str]:
        """
        Extract a section using flexible synonyms.
        Example: "plot" matches Plot, Story, Synopsis, etc.
        Returns cleaned text or None.
        """
        if not raw_text:
            return None

        # Normalize text for section detection
        lines = raw_text.splitlines()
        lower_lines = [ln.lower() for ln in lines]

        # Find target synonyms
        target = section_name.lower()
        synonyms = self._SECTION_SYNONYMS.get(target, [target])

        # Locate section header index
        start_idx = None
        for i, ln in enumerate(lower_lines):
            for syn in synonyms:
                if ln.strip().startswith(syn):
                    start_idx = i
                    break
            if start_idx is not None:
                break

        if start_idx is None:
            return None

        # Find next section header to know where to stop
        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            if lines[j].strip().endswith("==") or lines[j].strip().endswith(":"):
                end_idx = j
                break

        section_text = "\n".join(lines[start_idx:end_idx]).strip()
        return self.clean_wiki_text(section_text) if section_text else None
