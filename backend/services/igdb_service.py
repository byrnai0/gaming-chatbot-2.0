# filename: backend/services/igdb_service.py
from __future__ import annotations

import os
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables once at import time.
# Expected in .env:
#   IGDB_CLIENT_ID=<your twitch app client id>
#   IGDB_ACCESS_TOKEN=<your manual app access token>
load_dotenv()

IGDB_BASE = "https://api.igdb.com/v4"
CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
ACCESS_TOKEN = os.getenv("IGDB_ACCESS_TOKEN")

if not CLIENT_ID or not ACCESS_TOKEN:
    raise RuntimeError(
        "Missing IGDB_CLIENT_ID or IGDB_ACCESS_TOKEN in environment variables."
    )


def _fmt_epoch_to_date(epoch_seconds: Optional[int]) -> Optional[str]:
    """Convert IGDB epoch seconds to 'DD Mon YYYY' string (UTC-based)."""
    if not epoch_seconds:
        return None
    dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    return dt.strftime("%d %b %Y")


def _days_until(epoch_seconds: Optional[int]) -> Optional[int]:
    """Return whole days from today (local date) until the given epoch date.
    If date is in the past or None, returns None.
    """
    if not epoch_seconds:
        return None
    target = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).date()
    today = date.today()
    diff = (target - today).days
    return diff if diff > 0 else None


class IGDBService:
    """
    A small, dependency-free client around IGDB's v4 API with short-text helpers
    tailored for a gaming chatbot. All methods return plain strings suitable
    for direct display (R1).
    """

    def __init__(self) -> None:
        self.base = IGDB_BASE
        self.headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        }

    # ---------------------------
    # Low-level helpers
    # ---------------------------

    async def _post(self, endpoint: str, query: str) -> List[Dict[str, Any]]:
        """POST to an IGDB endpoint with a raw query string, return JSON list."""
        url = f"{self.base}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, data=query, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []

    async def _search_games_basic(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for candidate games, preferring main entries (exclude DLC/versions)."""
        # Note: IGDB "search" matches name and alternative_names.
        query = f'''
            search "{name}";
            fields id, name, first_release_date, popularity, version_parent, alternative_names.name;
            where version_parent = null;
            limit {limit};
        '''
        return await self._post("games", query)

    async def _pick_best_match(self, name: str) -> Optional[Dict[str, Any]]:
        """Pick the best match by popularity desc, then earliest first_release_date."""
        candidates = await self._search_games_basic(name)
        if not candidates:
            return None
        candidates.sort(
            key=lambda r: (
                -float(r.get("popularity") or 0.0),
                int(r.get("first_release_date") or 10**12),
            )
        )
        return candidates[0]

    # ---------------------------
    # High-level field fetchers
    # ---------------------------

    async def igdb_release_date(self, game_name: str, region_hint: Optional[str] = None) -> Optional[str]:
        """
        Return a short text release date.
        Preference order:
          1) Region match if region_hint provided (fuzzy match against 'human')
          2) Earliest known release date
          3) Fallback to game's first_release_date
        """
        game = await self._pick_best_match(game_name)
        if not game:
            return None

        # Fetch per-region release dates for better precision.
        q = f"""
            where game = {game['id']};
            fields date, human, region, platform;
            limit 50;
        """
        releases = await self._post("release_dates", q)

        # Try region hint (e.g., "NA", "North America", "EU", "Japan")
        if region_hint and releases:
            key = region_hint.lower()
            hits = [r for r in releases if isinstance(r.get("human"), str) and key in r["human"].lower()]
            if hits:
                hits.sort(key=lambda r: int(r.get("date") or 10**12))
                best = hits[0].get("date")
                fmt = _fmt_epoch_to_date(best)
                if fmt:
                    return fmt

        # Earliest across all known releases
        if releases:
            releases.sort(key=lambda r: int(r.get("date") or 10**12))
            earliest = releases[0].get("date")
            fmt = _fmt_epoch_to_date(earliest)
            if fmt:
                return fmt

        # Fallback: first_release_date on game
        return _fmt_epoch_to_date(game.get("first_release_date"))

    async def igdb_developer(self, game_name: str) -> Optional[str]:
        """Return the primary developer company name."""
        game = await self._pick_best_match(game_name)
        if not game:
            return None
        q = f"""
            where game = {game['id']} & developer = true;
            fields company.name;
            limit 10;
        """
        rows = await self._post("involved_companies", q)
        for row in rows:
            comp = row.get("company")
            if isinstance(comp, dict) and comp.get("name"):
                return comp["name"]
        return None

    async def igdb_platforms(self, game_name: str) -> Optional[str]:
        """Return a comma-separated list of platform names."""
        game = await self._pick_best_match(game_name)
        if not game:
            return None
        q = f"""
            where id = {game['id']};
            fields platforms.name;
            limit 1;
        """
        rows = await self._post("games", q)
        if not rows:
            return None
        platforms = rows[0].get("platforms") or []
        names: List[str] = []
        for p in platforms:
            if isinstance(p, dict) and p.get("name"):
                names.append(p["name"])
        return ", ".join(names) if names else None

    async def igdb_genres(self, game_name: str) -> Optional[str]:
        """Return a comma-separated list of genre names."""
        game = await self._pick_best_match(game_name)
        if not game:
            return None
        q = f"""
            where id = {game['id']};
            fields genres.name;
            limit 1;
        """
        rows = await self._post("games", q)
        if not rows:
            return None
        genres = rows[0].get("genres") or []
        names: List[str] = []
        for g in genres:
            if isinstance(g, dict) and g.get("name"):
                names.append(g["name"])
        return ", ".join(names) if names else None

    async def igdb_engine(self, game_name: str) -> Optional[str]:
        """Return the game engine name, if available."""
        game = await self._pick_best_match(game_name)
        if not game:
            return None
        q = f"""
            where id = {game['id']};
            fields game_engines.name;
            limit 1;
        """
        rows = await self._post("games", q)
        if not rows:
            return None
        engines = rows[0].get("game_engines") or []
        for e in engines:
            if isinstance(e, dict) and e.get("name"):
                return e["name"]
        return None

    async def igdb_rating(self, game_name: str) -> Optional[str]:
        """
        Return IGDB rating text. Prefers:
          - total_rating (combined)
          - aggregated_rating (critics)
          - rating (users)
        Output examples:
          - "IGDB: 93/100"
          - "Critic: 89/100, User: 91/100"
        """
        game = await self._pick_best_match(game_name)
        if not game:
            return None
        q = f"""
            where id = {game['id']};
            fields total_rating, aggregated_rating, rating;
            limit 1;
        """
        rows = await self._post("games", q)
        if not rows:
            return None

        row = rows[0]
        total = row.get("total_rating")
        critic = row.get("aggregated_rating")
        user = row.get("rating")

        # Round to nearest integer if present
        def r(x: Any) -> Optional[int]:
            try:
                return int(round(float(x)))
            except Exception:
                return None

        total_r = r(total)
        critic_r = r(critic)
        user_r = r(user)

        parts: List[str] = []
        if total_r is not None:
            parts.append(f"IGDB: {total_r}/100")
        if critic_r is not None:
            parts.append(f"Critic: {critic_r}/100")
        if user_r is not None:
            parts.append(f"User: {user_r}/100")

        return ", ".join(parts) if parts else None

    async def igdb_countdown(self, game_name: str, region_hint: Optional[str] = None) -> Optional[str]:
        """
        Return a detailed countdown for unreleased games (C2):
          "Releases on 15 Sep 2025 — 132 days from now"
        If already released, returns:
          "Released on 19 May 2015"
        """
        game = await self._pick_best_match(game_name)
        if not game:
            return None

        # Try to get the best/earliest regional release date
        q = f"""
            where game = {game['id']};
            fields date, human;
            limit 50;
        """
        releases = await self._post("release_dates", q)

        chosen_date: Optional[int] = None
        if releases:
            if region_hint:
                key = region_hint.lower()
                hits = [r for r in releases if isinstance(r.get("human"), str) and key in r["human"].lower()]
                if hits:
                    hits.sort(key=lambda r: int(r.get("date") or 10**12))
                    chosen_date = hits[0].get("date")
            if not chosen_date:
                releases.sort(key=lambda r: int(r.get("date") or 10**12))
                chosen_date = releases[0].get("date")

        if not chosen_date:
            chosen_date = game.get("first_release_date")

        # If we still don't have a date, give up
        if not chosen_date:
            return None

        fmt = _fmt_epoch_to_date(chosen_date)
        if not fmt:
            return None

        days = _days_until(chosen_date)
        if days is None:
            # Already released
            return f"Released on {fmt}"
        return f"Releases on {fmt} — {days} days from now"

    async def igdb_summary(self, game_name: str) -> Optional[str]:
        """
        Return a short factual summary (2–3 lines max) built from IGDB fields.
        The agent can optionally rewrite this into a more engaging two-liner.
        """
        game = await self._pick_best_match(game_name)
        if not game:
            return None

        q = f"""
            where id = {game['id']};
            fields name, first_release_date, genres.name, platforms.name, involved_companies.company.name, involved_companies.developer, game_engines.name, game_modes.name, player_perspectives.name;
            limit 1;
        """
        rows = await self._post("games", q)
        if not rows:
            return None

        row = rows[0]
        name: str = row.get("name") or game_name

        year = None
        if isinstance(row.get("first_release_date"), (int, float)):
            dt = datetime.fromtimestamp(int(row["first_release_date"]), tz=timezone.utc)
            year = dt.year

        # Collect fields safely
        def collect_names(items: Any) -> List[str]:
            names: List[str] = []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("name"):
                        names.append(it["name"])
            return names

        genres = collect_names(row.get("genres"))
        platforms = collect_names(row.get("platforms"))
        engines = collect_names(row.get("game_engines"))
        modes = collect_names(row.get("game_modes"))
        perspectives = collect_names(row.get("player_perspectives"))

        # Developer: prefer involved_companies where developer=true
        dev_name: Optional[str] = None
        ic = row.get("involved_companies") or []
        if isinstance(ic, list):
            for ent in ic:
                if isinstance(ent, dict) and ent.get("developer") and isinstance(ent.get("company"), dict):
                    dev_name = ent["company"].get("name")
                    if dev_name:
                        break

        # Build a compact, purely factual 2–3 line summary.
        bits: List[str] = []
        bits.append(f"{name}" + (f" ({year})" if year else ""))
        if dev_name:
            bits.append(f"Developer: {dev_name}")
        if genres:
            bits.append(f"Genres: {', '.join(genres[:3])}")
        if platforms:
            bits.append(f"Platforms: {', '.join(platforms[:4])}")
        if engines:
            bits.append(f"Engine: {engines[0]}")
        if modes:
            bits.append(f"Modes: {', '.join(modes[:2])}")
        if perspectives:
            bits.append(f"Perspective: {', '.join(perspectives[:2])}")

        # Join into <= 3 short sentences, trimming extras if needed.
        # Prioritize (title), developer, genres/platforms; then engine/modes/perspective if room.
        # Keep it simple—agent can rewrite further if needed.
        lines: List[str] = []
        if bits:
            lines.append(bits[0] + ".")
        if len(bits) > 1:
            lines.append(bits[1] + ".")
        if len(bits) > 2:
            lines.append(bits[2] + ".")
        if len(lines) < 3 and len(bits) > 3:
            lines.append(bits[3] + ".")

        return " ".join(lines) if lines else None
