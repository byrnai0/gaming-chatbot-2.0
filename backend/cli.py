from backend.main import agent_executor, parser  # re-use your existing chatbot logic
# CHANGED: Added continuous chat loop
print("Salutations, Gamer! Ask me anything about video games. Type 'exit' to quit.")
chat_history = []

while True:
    query = input("\nYou: ")
    
    if query.lower() in ['exit', 'quit']:
        print("GG! See you next time.")
        break
    
    if query.strip() == "":
        continue
    
    # CHANGED: Pass chat_history to maintain context
    res = agent_executor.invoke({"question": query, "chat_history": chat_history})
    
    # CHANGED: Update chat_history with the conversation
    chat_history.append(f"Human: {query}")
    
    try:
        response = parser.parse(res["output"])

        # CHANGED: Enhanced output formatting for different response types
        print(f"\nGaming Assistant:")

        if response.rawg_info:
            print(f"Real-time Data:\n{response.rawg_info}")

        
        if response.summary:
            print(f"Summary: {response.summary}\n")
        
        if response.no_spoilers:
            print(f"Spoiler-Free: {response.no_spoilers}\n")
            
        if response.spoilers:
            print(f"SPOILER ALERT: {response.spoilers}\n")
            
        if response.warning:
            print(f" {response.warning}\n")
            
        if response.lore:
            print(f"Lore: {response.lore}\n")
            
        if response.game_tips:
            print(f"Tips/Codes: {response.game_tips}\n")

        # CHANGED: Add AI response to chat history
        chat_history.append(f"AI: {res['output']}")
    except Exception as e:
        print("Error parsing response:", e)
        print("Raw response:", res["output"])
        # CHANGED: Add raw response to chat history if parsing fails
        chat_history.append(f"AI: {res['output']}")