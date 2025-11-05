# filename: backend/services/hltb_service.py
from __future__ import annotations

import asyncio
from typing import Optional

from howlongtobeatpy import HowLongToBeat


class HLTBService:
    """
    Thin wrapper around howlongtobeatpy. Runs sync search in a thread
    so our app stays async-friendly.
    """

    async def lengths(self, game_name: str) -> Optional[str]:
        def _search():
            return HowLongToBeat().search(game_name)

        # Run blocking search in a thread
        results = await asyncio.to_thread(_search)
        if not results:
            return None

        # pick best match by similarity
        best = max(results, key=lambda r: r.similarity)
        # Some results may not have all fields; guard with "or 0"
        main = best.main_story or 0
        main_extras = best.main_extra or 0
        comp = best.completionist or 0

        # Format short single line
        return f"Main: {int(main)}h | Main+Extras: {int(main_extras)}h | Completionist: {int(comp)}h"
