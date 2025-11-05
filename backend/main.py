# filename: backend/main.py
# Stage 2 – Wikipedia Tools Integrated + RAWG Tools (modular, async, silent)

from __future__ import annotations

import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool, StructuredTool

# IGDB + WIKI SERVICES
from backend.services.rawg_service import RAWGService
from backend.services.wiki_service import WikiService
from backend.services.hltb_service import HLTBService
from backend.services.plot_processing import (
    detect_spoiler_intent,
    extract_spoiler_free,
    extract_full_spoilers,
    condense_plot,
)

# ---------------- ENFORCEMENT MIDDLEWARE (Stage 3D) ----------------
from typing import Any
import re

async def run_agent(query: str, chat_history: list[str]):
    res = await agent_executor.ainvoke({"question": query, "chat_history": chat_history})
    parsed = parser.parse(res["output"])
    parsed = enforce_output_rules(parsed, query)
    return parsed

def enforce_output_rules(parsed: Response, user_query: str) -> Response:
    # Detect length interest (SMART)
    length_keywords = ["long", "short", "hours", "time to beat", "how long", "length"]
    if any(word in user_query.lower() for word in length_keywords):
        if parsed.topic in ["", None, "summary"]:
            parsed.topic = "metadata"

    """Enforce NS-Medium spoiler safety, field hygiene, and auto-soft topic corrections."""

    # 1. Auto-soft Topic Detection if missing
    if not parsed.topic:
        uq = user_query.lower()
        if any(word in uq for word in ["release", "platform", "developer", "engine", "rating", "metacritic"]):
            parsed.topic = "metadata"
        elif "character" in uq:
            parsed.topic = "characters"
        elif "lore" in uq or "world" in uq:
            parsed.topic = "lore"
        elif "dlc" in uq or "expansion" in uq:
            parsed.topic = "dlc"
        elif "ending" in uq or "spoil" in uq:
            parsed.topic = "spoilers"
        elif "story" in uq or "plot" in uq:
            parsed.topic = "plot"
        elif "gameplay" in uq or "mechanic" in uq or "combat" in uq:
            parsed.topic = "gameplay"
        elif any(word in uq for word in ["how to", "beat", "solve", "puzzle", "tips", "guide"]):
            parsed.topic = "tips"

    # 2. Prevent spoiler leakage into no_spoilers
    spoiler_trigger_words = ["kills", "dies", "death", "betray", "twist", "ending", "final boss", "reveals"]
    if parsed.no_spoilers:
        if any(word in parsed.no_spoilers.lower() for word in spoiler_trigger_words):
            # Move content into spoilers
            parsed.spoilers = (parsed.spoilers + "\n" + parsed.no_spoilers).strip()
            parsed.no_spoilers = ""
            parsed.warning = parsed.warning or "Contains major spoilers"

    # 3. If spoilers exist but no warning, auto-add warning
    if parsed.spoilers and not parsed.warning:
        parsed.warning = "Contains major spoilers"

    # 4. NS-Medium enforcement — re-filter no_spoilers if plot topic
    if parsed.topic == "plot" and parsed.no_spoilers:
        parsed.no_spoilers = extract_spoiler_free(parsed.no_spoilers)

    # 5. Remove accidental fields or hallucinated content
    allowed_fields = set(Response.__fields__.keys())
    for field in list(parsed.__dict__.keys()):
        if field not in allowed_fields:
            del parsed.__dict__[field]

    return parsed



load_dotenv()

# ---------------- Pydantic Model ----------------
class Response(BaseModel):
    summary: str = ""
    spoilers: str = ""
    no_spoilers: str = ""
    game_tips: str = ""
    lore: str = ""
    warning: str = ""
    rawg_data: str = ""      # short RAWG metadata line
    game_length: str = ""     # HLTB length (3-line HL3 format)
    wiki_data: str = ""      # NEW: short wiki extracted text
    can_be_spoiler: bool = False # If topic is spoiler-sensitive
    topic: str = ""              # Detected topic: metadata, plot, spoilers, characters, development, lore, gameplay, tips, dlc

# ---------------- LLM + Parser ----------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, verbose=False, timeout=30)
parser = PydanticOutputParser(pydantic_object=Response)


# ---------------- Service Instances ----------------
_rawg = RAWGService()
_wiki = WikiService()
_hltb = HLTBService()

# ---------------- RAWG TOOLS (metadata short answers) ----------------
async def _t_release_date(game_name: str) -> str:
    return await _rawg.release_date(game_name) or "Release date not found."

async def _t_countdown(game_name: str) -> str:
    return await _rawg.countdown(game_name) or "No release date available."

async def _t_developer(game_name: str) -> str:
    return await _rawg.developer(game_name) or "Developer not found."

async def _t_platforms(game_name: str) -> str:
    return await _rawg.platforms(game_name) or "Platforms not found."

async def _t_genres(game_name: str) -> str:
    return await _rawg.genres(game_name) or "Genres not found."

async def _t_tags(game_name: str) -> str:
    return await _rawg.tags(game_name) or "Tags not found."

async def _t_rating(game_name: str) -> str:
    return await _rawg.rating(game_name) or "Rating not found."

async def _t_summary(game_name: str) -> str:
    return await _rawg.summary(game_name) or "Summary unavailable."



# ---------------- WIKIPEDIA TOOLS (NEW – Stage 2) ----------------
async def _t_wiki_fetch_raw(title: str) -> str:
    """Fetch full wiki page plain text."""
    return await _wiki.fetch_wiki_page_raw(title) or "No Wikipedia page found."

def _t_wiki_extract_section(raw_text: str, section_name: str) -> str:
    """Extract specific section text (Plot, Characters, Development, Gameplay)."""
    return _wiki.extract_section(raw_text, section_name) or "Section not found."

def _t_wiki_clean_text(text: str) -> str:
    """Clean Wiki text by stripping citations and extra formatting."""
    return _wiki.clean_wiki_text(text)

# ---------------- HLTB TOOL (game length) ----------------
async def _t_hltb_lengths(game_name: str) -> str:
    return await _hltb.lengths(game_name) or "Length not found."

def _wiki_extract_section_tool(raw_text: str, section_name: str) -> str:
    return _t_wiki_extract_section(raw_text, section_name)


# ---------------- TOOL REGISTRY ----------------
tools = [
    # ---- RAWG SHORT FACT TOOLS ----
    Tool(
        name="rawg_release_date",
        description="Short release date. Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_release_date(game_name),
    ),
    Tool(
        name="rawg_countdown",
        description="Release countdown or release date. Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_countdown(game_name),
    ),
    Tool(
        name="rawg_developer",
        description="Short primary developer(s). Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_developer(game_name),
    ),
    Tool(
        name="rawg_platforms",
        description="Short comma-separated platforms. Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_platforms(game_name),
    ),
    Tool(
        name="rawg_genres",
        description="Short comma-separated genres. Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_genres(game_name),
    ),
    Tool(
        name="rawg_tags",
        description="Short comma-separated tags. Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_tags(game_name),
    ),
    Tool(
        name="rawg_rating",
        description="RAWG rating summary (RAWG/5, ratings count, Metacritic if present). Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_rating(game_name),
    ),
    Tool(
        name="rawg_summary",
        description="Factual 2–3 line summary from RAWG fields. Input: game_name.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_summary(game_name),
    ),

    # ---- HLTB GAME LENGTH ----
    Tool(
        name="hltb_lengths",
        description="Game length from HowLongToBeat. Input: game_name. Returns 'Main | Main+Extras | Completionist'.",
        func=lambda *_, **__: "use coroutine",
        coroutine=lambda game_name: _t_hltb_lengths(game_name),
    ),

    # ---- WIKIPEDIA RAW + SECTION TOOLS (KEEP AS IS) ----
    Tool(
    name="wiki_fetch_raw",
    description=(
        "Fetch full raw Wikipedia page text. Input: title. "
        "Use this BEFORE requesting plot/characters/dev info."
    ),
    func=lambda *_, **__: "use coroutine",
    coroutine=lambda title: _t_wiki_fetch_raw(title),
    ),
    StructuredTool.from_function(
    name="wiki_extract_section",
    description=(
        "Extract a section from raw Wikipedia text. "
        "Arguments: raw_text (string), section_name (string). "
        "Examples: plot, characters, development, gameplay, dlc."
    ),
    func=_wiki_extract_section_tool,
    ),
    Tool(
    name="wiki_clean_text",
    description="Clean wiki text: remove [1], [2], etc. Input: text.",
    func=lambda text: _t_wiki_clean_text(text),
    ),  
]



# ---------------- UPDATED PROMPT ----------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert gaming assistant.

Your #1 rule: Answer ONLY what the user asked for. Keep responses short, precise, and avoid unnecessary information.

### TOPIC CLASSIFICATION RULES
• For every user request, classify it into ONE topic and set the 'topic' field accordingly.
• Valid topics: metadata, plot, spoilers, characters, development, lore, gameplay, tips, dlc
• Use the topic to decide which tools and fields to use.
• Examples:
  - “When was Elden Ring released?” → metadata
  - “Explain the story of Elden Ring” → plot
  - “Spoil the ending of Elden Ring” → spoilers
  - “Who are the characters in God of War 3?” → characters
  - “How was GTA V developed?” → development
  - “What's the lore of Dark Souls?” → lore
  - “How do I beat Malenia?” → tips
  - “List Witcher 3 DLCs” → dlc

### DATA SOURCE RULES
• Use RAWG tools ONLY for metadata:
  Release date, developer, platforms, genres, tags, rating, countdown, factual summaries
• Use HowLongToBeat (hltb_lengths) for:
  Game length (Main / Main+Extras / Completionist)
• Use Wikipedia tools for:
  Plot/story, character info, development history, world/lore, gameplay details, DLC info
• For plot/story:
  ALWAYS call wiki_fetch_raw first, then wiki_extract_section('plot'), then rewrite

### SPOILER HANDLING — NS-MEDIUM POLICY
• Default: Do NOT provide spoilers unless the user clearly requests them
• If topic=plot (no spoiler request):
  - Provide a spoiler-free retelling in 'no_spoilers'
  - Include only early premise + setup
  - Remove twists, late-game events, and endings
• If topic=spoilers:
  - Provide the full plot in 'spoilers'
  - Add a 'warning' field: "Contains major spoilers"
  - Do not place any spoiler content in 'no_spoilers'
• Never mix spoiler and non-spoiler content together

### PLOT ROUTING LOGIC
If topic=plot (no spoiler intent):
  1) Use wiki_fetch_raw
  2) Use wiki_extract_section('plot')
  3) Apply spoiler-free processing (trim twists, ending)
  4) Place result into 'no_spoilers'

If topic=spoilers:
  1) Use wiki_fetch_raw
  2) Use wiki_extract_section('plot')
  3) Use full plot (no trimming)
  4) Place in 'spoilers' + add 'warning'

### FIELD USAGE RULES
•  'rawg_data' → Store RAWG metadata output (short factual line)
• 'wiki_data' → Short extracted wiki content before rewriting (if needed)
• 'summary' → A short 1-2 sentence AI rewrite/overview when user wants a general explanation
• 'no_spoilers' → Spoiler-free plot only
• 'spoilers' → Only when requested
• 'lore' → Use for worldbuilding, universe history, backstory, mythology, timelines
• 'game_tips' → Only for help, guides, puzzles, combat strategies, or how to beat something

### DLC RULES
• For DLC requests, treat the topic as dlc
• Use Wikipedia only to extract and summarize DLCs and expansions
• Do not include spoilers about DLC unless user explicitly asks

### INTERNAL TOOL & PROCESSING RULES (NEVER REVEAL TO USER)
• First decide the topic
• Then choose RAWG, HLTB, or Wikipedia tools based on topic
• Use spoiler-processing logic internally when writing output
• Do NOT mention tool names, internal functions, or reasoning
• Your final response must strictly follow the Pydantic schema

### RESPONSE FORMAT
Return the response using the Pydantic format below — do NOT add extra fields:
{format_instructions}
""",
        ),
        "{chat_history}",
        "{question}",
        "{agent_scratchpad}",
    ]
).partial(format_instructions=parser.get_format_instructions())



# ---------------- AGENT + EXECUTOR ----------------
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools,
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
