# filename: backend/api.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.main import agent_executor, parser, enforce_output_rules

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list[str] = []

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        # Use async invoke to support async tools
        res = await agent_executor.ainvoke({"question": req.message, "chat_history": req.history})
        parsed = parser.parse(res["output"])
        parsed = enforce_output_rules(parsed, req.message)


        final_response = ""
        if parsed.rawg_data:
            final_response += f"{parsed.rawg_data}\n\n"
        if parsed.summary:
            final_response += f"{parsed.summary}\n\n"
        if parsed.no_spoilers:
            final_response += f"{parsed.no_spoilers}\n\n"
        if parsed.spoilers:
            final_response += f"⚠️ SPOILERS: {parsed.spoilers}\n\n"
        if parsed.lore:
            final_response += f"{parsed.lore}\n\n"
        if parsed.game_tips:
            final_response += f"{parsed.game_tips}\n\n"

        return ChatResponse(response=final_response.strip())
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")
