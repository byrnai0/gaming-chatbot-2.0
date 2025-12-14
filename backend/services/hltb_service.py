from __future__ import annotations

from howlongtobeatpy import HowLongToBeat

class HLTBService:
    async def lengths(self, game_name: str) -> str:
        """Safe wrapper around HLTB async search. Never throws."""
        
        try:
            # Use async_search directly (not search() with to_thread)
            results = await HowLongToBeat().async_search(game_name)
            
            if not results or len(results) == 0:
                return None
            
            # Get best match by similarity
            best = max(results, key=lambda element: element.similarity)
            
            # Format output with proper handling
            main = f"{best.main_story} hours" if best.main_story else "N/A"
            plus = f"{best.main_extra} hours" if best.main_extra else "N/A"
            comp = f"{best.completionist} hours" if best.completionist else "N/A"
            
            return f"Main: {main} | Main+Extras: {plus} | Completionist: {comp}"
            
        except Exception as e:
            # HLTB breaks often — just return None instead of throwing
            print(f"HLTB error: {e}")
            return None
