from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

class Response(BaseModel):
    summary: str
    spoilers: str = ""  # CHANGED: Made optional with default
    no_spoilers: str = ""  # CHANGED: Made optional with default  
    game_tips: str = ""  # CHANGED: Added for codes/puzzles
    lore: str = ""  # CHANGED: Added for detailed lore
    warning: str = ""  # CHANGED: Added for spoiler warnings

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, verbose=False)
parser = PydanticOutputParser(pydantic_object= Response)

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
	        5. BASIC INFORMATION: Provide with the basic and recommended system requirements to play the game and other information related to the game when the user asks 
            
            RESPONSE GUIDELINES:
            - Be conversational and engaging - like a fellow gamer
            - Use natural language and gaming terminology
            - If unsure about spoilers, ask for clarification
            - Mark spoiler content clearly
            - Provide practical, useful gaming advice
            - Only discuss video games and related content

            FORMAT: Provide responses in this structured format:
            {format_instructions}
            """
            ),  
            (placeholder1 := "{chat_history}"),
            (human := "{question}"),
            (placeholder2 := "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools = [],
)

agent_executor=AgentExecutor(agent=agent, tools=[], verbose=False)
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