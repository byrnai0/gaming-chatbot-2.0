# rawg service for game metadata
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

RAWG_BASE = "https://api.rawg.io/api"
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

if not RAWG_API_KEY:
    raise RuntimeError("Missing RAWG_API_KEY in .env")


def _fmt_date(yyyy_mm_dd: Optional[str]) -> Optional[str]:
    if not yyyy_mm_dd:
        return None
    try:
        dt = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return yyyy_mm_dd 


def _days_until(yyyy_mm_dd: Optional[str]) -> Optional[int]:
    if not yyyy_mm_dd:
        return None
    try:
        target = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").date()
        today = date.today()
        d = (target - today).days
        return d if d > 0 else None
    except Exception:
        return None


class RAWGService:
    """
    Minimal async RAWG client for short-text answers.
    No OAuth; uses RAWG_API_KEY from .env.
    """

    def __init__(self) -> None:
        self.base = RAWG_BASE
        self.key = RAWG_API_KEY
        self.headers = {"Accept": "application/json"}

    # low level helpers

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any] | List[Dict[str, Any]] | None:
        url = f"{self.base}/{path.lstrip('/')}"
        q = {"key": self.key, **params}
        async with httpx.AsyncClient(timeout=20.0, headers=self.headers) as client:
            r = await client.get(url, params=q)
            r.raise_for_status()
            return r.json()

    async def _search_best(self, name: str) -> Optional[Dict[str, Any]]:
        # Search games (page_size=1) for best match
        data = await self._get("games", {"search": name, "page_size": 1})
        if not isinstance(data, dict):
            return None
        results = data.get("results") or []
        return results[0] if results else None

    async def _get_details(self, game_slug_or_id: str | int) -> Optional[Dict[str, Any]]:
        # RAWG supports slug or numeric id
        data = await self._get(f"games/{game_slug_or_id}", {})
        if isinstance(data, dict) and data.get("id"):
            return data
        return None

    # high level methods

    async def release_date(self, game_name: str) -> Optional[str]:
        hit = await self._search_best(game_name)
        if not hit:
            return None
        return _fmt_date(hit.get("released"))

    async def countdown(self, game_name: str) -> Optional[str]:
        hit = await self._search_best(game_name)
        if not hit:
            return None
        rel = hit.get("released")
        fmt = _fmt_date(rel)
        if not fmt:
            return None
        days = _days_until(rel)
        if days is None:
            return f"Released on {fmt}"
        return f"Releases on {fmt} — {days} days from now"

    async def developer(self, game_name: str) -> Optional[str]:
        hit = await self._search_best(game_name)
        if not hit:
            return None
        details = await self._get_details(hit.get("slug") or hit.get("id"))
        if not details:
            return None
        devs = details.get("developers") or []
        names = [d.get("name") for d in devs if isinstance(d, dict) and d.get("name")]
        return ", ".join(names) if names else None

    async def platforms(self, game_name: str) -> Optional[str]:
        hit = await self._search_best(game_name)
        if not hit:
            return None
        plats = hit.get("platforms") or []
        names: List[str] = []
        for p in plats:
            plat = p.get("platform") if isinstance(p, dict) else None
            if isinstance(plat, dict) and plat.get("name"):
                names.append(plat["name"])
        return ", ".join(names) if names else None

    async def genres(self, game_name: str) -> Optional[str]:
        hit = await self._search_best(game_name)
        if not hit:
            return None
        gens = hit.get("genres") or []
        names = [g.get("name") for g in gens if isinstance(g, dict) and g.get("name")]
        return ", ".join(names) if names else None

    async def tags(self, game_name: str) -> Optional[str]:
        # tags available in details
        hit = await self._search_best(game_name)
        if not hit:
            return None
        details = await self._get_details(hit.get("slug") or hit.get("id"))
        if not details:
            return None
        tags = details.get("tags") or []
        names = [t.get("name") for t in tags if isinstance(t, dict) and t.get("name")]
        return ", ".join(names[:10]) if names else None

    async def rating(self, game_name: str) -> Optional[str]:
        hit = await self._search_best(game_name)
        if not hit:
            return None
        # RAWG fields
        rating = hit.get("rating")          # average user rating out of 5
        ratings_count = hit.get("ratings_count")
        metacritic = hit.get("metacritic")
        parts: List[str] = []
        if isinstance(rating, (int, float)):
            parts.append(f"RAWG: {round(float(rating), 2)}/5")
        if isinstance(ratings_count, int):
            parts.append(f"{ratings_count} ratings")
        if isinstance(metacritic, int):
            parts.append(f"Metacritic: {metacritic}/100")
        return ", ".join(parts) if parts else None

    async def summary(self, game_name: str) -> Optional[str]:
        # 2–3 lines of basic metadata
        hit = await self._search_best(game_name)
        if not hit:
            return None
        details = await self._get_details(hit.get("slug") or hit.get("id"))
        if not details:
            return None

        name = details.get("name") or game_name
        released = _fmt_date(details.get("released"))
        gens = [g.get("name") for g in (details.get("genres") or []) if g.get("name")]
        plats = [p.get("name") for p in (details.get("platforms") or []) if p.get("name")]
        # RAWG description_raw is available at /games/{id}
        desc = details.get("description_raw") or ""
        # Build 2–3 short lines
        bits: List[str] = []
        bits.append(f"{name}" + (f" ({released})" if released else ""))
        if gens:
            bits.append(f"Genres: {', '.join(gens[:3])}")
        if plats:
            bits.append(f"Platforms: {', '.join(plats[:4])}")

        return " ".join([b + "." for b in bits[:3]]).strip()
