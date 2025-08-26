from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

class Response(BaseModel):
    topic: str
    summary: str
    spoilers: str
    noSpoilers: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, verbose=False)
parser = PydanticOutputParser(pydantic_object= Response)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Due to years of research and studies, you have become an expert in the field of video games.
            Now you are a gaming assistant that provides information about video games as per user requests.
            When asked about the plot of a game, you will default to providing a summary without spoilers.
            However, if the user specifically requests spoilers, you will provide a separate section with spoilers included.
            If the user requests for the full lore of a game, you will ask the user to clarify if they want spoilers or not, and provide both sections fully and detailed.
            When asked about any part of a game, be it the gameplay, characters,  or development, you will provide accurate and detailed information.
            Wrap the output in the following format: \n{format_instructions} and nothing else.
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
query = input("Enter your question: ")
res = agent_executor.invoke({"question": query, "chat_history": []})

try:
    response=parser.parse(res["output"])
    print(response.model_dump_json(indent=4))
except Exception as e:
    print("Error parsing response:", e)
    print("Raw response:", res["output"])

