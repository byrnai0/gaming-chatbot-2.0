#file for cli interaction
import asyncio
from backend.main import agent_executor, parser, enforce_output_rules
from backend.formatters.response_formatter import format_response

async def chat_loop():
    print("Gaming Assistant is ready. Type 'exit' to quit.")
    chat_history = []

    while True:
        query = input("\nYou: ").strip()
        if query.lower() in ["exit", "quit"]:
            print("Good game. Catch you later!")
            break
        if not query:
            continue

        # Run agent
        res = await agent_executor.ainvoke({"question": query, "chat_history": chat_history})

        # Parse Pydantic
        try:
            parsed = parser.parse(res["output"])
        except Exception:
            print("\n[Error: Could not parse AI response]")
            print(res["output"])
            continue

        # Enforce safety rules
        parsed = enforce_output_rules(parsed, query)

        # Convert into human-friendly text
        final_text = format_response(parsed)

        print(f"\n{final_text}")

        # Store full LLM output into history
        chat_history.append(f"Human: {query}")
        chat_history.append(f"AI: {res['output']}")

if __name__ == "__main__":
    asyncio.run(chat_loop())
