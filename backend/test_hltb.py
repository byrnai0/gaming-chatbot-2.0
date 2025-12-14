# Create a test file: test_hltb.py
import asyncio
from howlongtobeatpy import HowLongToBeat

async def test():
    try:
        results = await HowLongToBeat().async_search("Days Gone")
        print(f"Results: {results}")
        if results:
            print(f"Found {len(results)} games")
            best = max(results, key=lambda x: x.similarity)
            print(f"Best match: {best.game_name}")
            print(f"Main story: {best.main_story}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
