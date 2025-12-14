from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.main import run_agent

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class QueryRequest(BaseModel):
    query: str

# Response endpoint
@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """Handle user queries and return gaming info."""
    try:
        # Run your agent with empty chat history
        result = await run_agent(request.query, chat_history=[])
        
        # Convert Pydantic Response to dict
        return result.dict()
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Gaming Assistant API is running"}
