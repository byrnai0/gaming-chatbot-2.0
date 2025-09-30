from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool
import requests
import os
import time

load_dotenv()

class Response(BaseModel):
    summary: str
    spoilers: str = ""  # CHANGED: Made optional with default
    no_spoilers: str = ""  # CHANGED: Made optional with default  
    game_tips: str = ""  # CHANGED: Added for codes/puzzles
    lore: str = ""  # CHANGED: Added for detailed lore
    warning: str = ""  # CHANGED: Added for spoiler warnings'
    rawg_info: str = ""  # CHANGED: Added for rawg.io data

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, verbose=False, timeout=30)
parser = PydanticOutputParser(pydantic_object= Response)

# CHANGED: RAWG.io API Tool Implementation
def search_rawg_games(game_name: str) -> str:
    """Search for game information using RAWG.io API"""
    try:
        api_key = os.getenv("RAWG_API_KEY")
        if not api_key:
            return "RAWG_API_KEY not found in environment variables. Please add your API key to .env file."
        print(f"🔍 Searching RAWG.io for: {game_name}...")
        # Search for the game
        search_url = f"https://api.rawg.io/api/games?key={api_key}&search={game_name}&page_size=1"
        response = requests.get(search_url, timeout=10)
        
        if response.status_code != 200:
            return f"API Error: {response.status_code}"
        
        data = response.json()
        
        if not data['results']:
            return f"No game found with name: {game_name}"
        
        game = data['results'][0]
        game_id = game['id']
        
        # Get detailed information
        details_url = f"https://api.rawg.io/api/games/{game_id}?key={api_key}"
        details_response = requests.get(details_url, timeout=10)
        details_data = details_response.json()
        
        # Format the response
        game_info = f"""
            GAME INFORMATION FROM RAWG.IO:

            Title: {game['name']}
            Released: {game.get('released', 'Not available')}
            Rating: {game.get('rating', 'N/A')}/5 ({game.get('ratings_count', 0)} ratings)
            Metacritic: {details_data.get('metacritic', 'N/A')}/100
            Platforms: {', '.join([p['platform']['name'] for p in game['platforms']]) if game['platforms'] else 'Not specified'}

            Description: {details_data.get('description_raw', game.get('description', 'No description available'))[:500]}...

            Genres: {', '.join([g['name'] for g in game['genres']]) if game['genres'] else 'Not specified'}
            Developers: {', '.join([d['name'] for d in details_data.get('developers', [])]) if details_data.get('developers') else 'Not specified'}
            Publishers: {', '.join([p['name'] for p in details_data.get('publishers', [])]) if details_data.get('publishers') else 'Not specified'}

            Playtime: {details_data.get('playtime', 'N/A')} hours average
            """
        return game_info
        
    except Exception as e:
        return f"Error fetching game data: {str(e)}"
    
    # CHANGED: Create RAWG.io tool
rawg_tool = Tool(
    name="rawg_game_search",
    description="Search for detailed game information from RAWG.io database including release dates, ratings, playtime, descriptions, and more",
    func=search_rawg_games
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an expert gaming assistant with deep knowledge of video games across all platforms and genres.
            
            CORE RESPONSIBILITIES:
            1. GAME SUMMARIES: Provide concise overviews of games including gameplay, story, and features
            2. LORE & STORY: 
               - Default: Provide lore without spoilers
               - If user asks for spoilers: Provide detailed spoiler-filled lore in 'spoilers' field
               - Always include a spoiler warning when giving spoilers
            3. GAME HELP: Provide codes, cheats, puzzle solutions, and tips when requested
            4. CHARACTERS & WORLD: Detailed information about game characters, worlds, and lore
            5. REAL-TIME DATA: Use the RAWG.io tool to get accurate, up-to-date game information when needed
            
            RESPONSE GUIDELINES:
            - Be conversational and engaging - like a fellow gamer
            - Don't repeat full introductions in follow-up questions
            - Use natural language and gaming terminology
            - If unsure about spoilers, ask for clarification
            - Mark spoiler content clearly
            - Provide practical, useful gaming advice
            - Use the RAWG.io tool for factual game data like release dates, ratings, platforms
            - Only discuss video games and related content, strictly avoid other topics
            
            WHEN TO USE RAWG.IO TOOL:
            - When user asks about game details, release dates, platforms
            - When you need accurate, up-to-date game information
            - When user asks "what platforms is [game] on?" or "when was [game] released? or "playtime of [game]?"
            
            FORMAT: Provide responses in this structured format:
            {format_instructions}
            """
            ),  
            (placeholder1 := "{chat_history}"),
            (human := "{question}"),
            (placeholder2 := "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# CHANGED: Added tools to agent creation
tools = [rawg_tool]  # CHANGED: Initialize tools list

agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools = tools,
)

agent_executor=AgentExecutor(agent=agent, tools=tools, verbose=True)
# CHANGED: Added continuous chat loop
print("Welcome to the Gaming Assistant! Type 'exit' or 'quit' to end the conversation.")
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
        print(f"\n🎮 Gaming Assistant:")

        if response.rawg_info:  # changed from response.rawg_data
            print(f"📊 Real-time Data:\n{response.rawg_info}")

        
        if response.summary:
            print(f"Summary: {response.summary}")
        
        if response.no_spoilers:
            print(f"Spoiler-Free: {response.no_spoilers}")
            
        if response.spoilers:
            print(f"SPOILER ALERT: {response.spoilers}")
            
        if response.warning:
            print(f" {response.warning}")
            
        if response.lore:
            print(f"Lore: {response.lore}")
            
        if response.game_tips:
            print(f"Tips/Codes: {response.game_tips}")

        # CHANGED: Add AI response to chat history
        chat_history.append(f"AI: {res['output']}")
    except Exception as e:
        print("Error parsing response:", e)
        print("Raw response:", res["output"])
        # CHANGED: Add raw response to chat history if parsing fails
        chat_history.append(f"AI: {res['output']}")