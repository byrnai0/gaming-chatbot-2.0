# filename: backend/cli.py

import asyncio
from backend.main import agent_executor, parser, enforce_output_rules

print("Salutations, Gamer! Ask me anything about video games. Type 'exit' to quit.")
chat_history: list[str] = []

async def chat_loop():
    while True:
        query = input("\nYou: ")

        if query.lower() in ["exit", "quit"]:
            print("GG! See you next time.")
            break

        if not query.strip():
            continue

        # Use async invoke for async tools
        res = await agent_executor.ainvoke({"question": query, "chat_history": chat_history})

        chat_history.append(f"Human: {query}")

        try:
            response = parser.parse(res["output"])
            response = enforce_output_rules(response, query)

            print(f"\nGaming Assistant:")

            if response.rawg_data:
                print(f"{response.rawg_data}")

            if response.summary:
                print(f"Summary: {response.summary}\n")

            if response.no_spoilers:
                print(f"Spoiler-Free: {response.no_spoilers}\n")

            if response.spoilers:
                print(f"SPOILER ALERT: {response.spoilers}\n")

            if response.warning:
                print(f"{response.warning}\n")

            if response.lore:
                print(f"Lore: {response.lore}\n")

            if response.game_tips:
                print(f"Tips/Codes: {response.game_tips}\n")

            chat_history.append(f"AI: {res['output']}")
        except Exception as e:
            print("Error parsing response:", e)
            print("Raw response:", res.get("output"))
            chat_history.append(f"AI: {res.get('output')}")

if __name__ == "__main__":
    asyncio.run(chat_loop())
