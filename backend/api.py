# api file for backend handling
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from backend.main import agent_executor, parser, enforce_output_rules
from backend.formatters.response_formatter import format_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str  # Changed from 'message' to match frontend
    history: list[str] = []

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        # Use 'query' to match what frontend sends
        res = await agent_executor.ainvoke({
            "question": req.query,  # Changed from req.message
            "chat_history": req.history
        })

        # Parse structured model
        parsed = parser.parse(res["output"])

        # Enforce rules
        parsed = enforce_output_rules(parsed, req.query)  # Changed from req.message

        # Format to human text
        final = format_response(parsed)

        return ChatResponse(response=final)

    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")
