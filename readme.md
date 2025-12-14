# Gaming Chatbot 2.0

A modular, AI-driven gaming information assistant designed to provide structured, accurate, and spoiler-controlled responses to user queries about video games.  
This project focuses on **backend intelligence**, data retrieval, personalized recommendations, and response moderation using a tool-calling LLM architecture.

---

## 1. Project Overview

Gaming Chatbot 2.0 is an intelligent system that answers user questions related to video games by integrating multiple external data sources and applying controlled natural-language processing.  

The primary objectives of this project are:

- To provide verified factual game information using external APIs
- To extract and summarize game content in a **spoiler-safe** manner
- To recommend similar games based on user preferences and gameplay patterns
- To retrieve real-time game information from community-driven sources
- To demonstrate the use of **LLM tool-calling**, modular service architecture, and controlled output formatting
- To enable both CLI-based interaction and REST API access for future UI integration

This project is currently developed as part of an academic initiative to demonstrate AI-assisted information systems and modular backend design.

## 2. Key Features (Current Implementation)

### ✅ Data Retrieval & Processing
| Source | Usage |
|--------|--------|
| **RAWG API** | Metadata including release date, developers, platforms, genres, tags, and ratings |
| **HowLongToBeat (HLTB)** | Game length for Main Story, Main + Extras, and Completionist modes |
| **Wikipedia API** | Plot, characters, lore, gameplay, development history, and DLC information |
| **Fandom API** | Deep game knowledge including walkthroughs, puzzle solutions, character details, and lore databases |

### ✅ AI Framework & Processing
- **LLM Tool-Calling Architecture** using LangChain
- **Structured Pydantic Output Model** for consistent response formatting
- **Spoiler Moderation System (NS-Medium Policy)**:
  - Summarizes plot spoiler-free unless requested
  - Automatically filters or relocates spoiler content
  - Adds warnings when spoilers are present
- **Post-Generation Enforcement Layer** ensuring:
  - Field hygiene (no hallucinated fields)
  - Topic alignment
  - Spoiler-safety checks

### ✅ Intelligent Recommendation System
- **Similar Game Recommendation Engine**:
  - Suggests games based on genre, gameplay mechanics, and thematic similarity
  - Example: User likes *Persona 5 Royal* → Recommends *Kingdom Hearts*, *Expeditions 33*, *Tokyo Xanadu*
  - Uses hybrid filtering combining content-based and collaborative approaches
- **Semantic Search Integration**:
  - Analyzes game descriptions, tags, and player reviews
  - Identifies hidden gems matching user preferences

### ✅ Interaction Modes
- **CLI Chat Interface** for local interaction
- **FastAPI Endpoint** (`/chat`) for system integration or frontend connectivity

---

## 3. System Architecture

### 3.1 High-Level Architecture

'''
User
│
▼
LLM Agent (Tool-Calling with Topic Routing)
│
├── RAWG Service (metadata)
├── HLTB Service (lengths)
├── Wikipedia Service (content extraction)
├── Spoiler Processing Module
├── Fandom Service (deep game knowledge)
└── Recommendation Engine (similar games)
│
▼
Response Enforcement Layer → Pydantic Model → Final Output
'''

### 3.2 Codebase Structure

'''
backend/
│
├── main.py # Agent, tools, system prompt, Pydantic model, enforcement
├── cli.py # Local CLI interface
├── api.py # FastAPI server
│
├── services/ # External service integrations
│ ├── rawg_service.py
│ ├── wiki_service.py
│ ├── hltb_service.py
│ ├── fandom_service.py
│ ├── plot_processing.py
│ └── recommendation_engine.py
│
├── formatters/
│ └── response_formatter.py # Converts model output to user-friendly text
│
└── init.py
'''

---

## 4. Technology Stack

| Category | Tools/Frameworks |
|----------|------------------|
| Language | Python 3.13 |
| Web Framework | FastAPI + Uvicorn |
| AI Framework | LangChain (Tool-Calling Agent) |
| Model | OpenAI `gpt-4o-mini` |
| Networking | HTTPX (async) |
| Data Sources | RAWG, HowLongToBeat, Wikipedia, Fandom |
| Validation | Pydantic |
| Environment Config | python-dotenv |

---

### 5. Future Enhancements (Planned Work)

The following items have been identified for future implementation:

| Planned Feature | Description |
|----------------|-------------|
| Steam API Integration | Player counts, reviews, price information, and community ratings |
| Metacritic Integration | Professional critic scores and aggregated review data |
| PlayStation Store / Xbox Store Integration | Console-specific pricing, availability, and exclusive content information |
| Reddit Community Sentiment Analysis | Real-time community opinions and discussions from gaming subreddits |
| Price Tracking & Deal Alerts | Notify users when games go on sale across multiple platforms |
| Achievement/Trophy Guide Integration | Comprehensive guides to help users complete games 100% |
| Release Calendar Integration | Upcoming game releases with personalized notifications and reminders |
| Voice Integration | Speech-to-text for hands-free interaction |
| Multilingual Support | Support for multiple languages |
| User Profile System | Persistent user preferences and history tracking |

## 6. Acknowledgements

- RAWG.io for metadata
- HowLongToBeat for playtime information
- Wikipedia for reference data
- Fandom for community-driven game knowledge
- OpenAI and LangChain for AI tooling