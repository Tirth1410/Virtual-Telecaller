import asyncio
import edge_tts
import nest_asyncio

import io
# import pygame
import edge_tts
import asyncio
import nest_asyncio
import os
from dotenv import load_dotenv
# import speech_recognition as sr
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_community.vectorstores import FAISS
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from typing import Literal, TypedDict, List
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from pinecone import Pinecone
import uuid

from helper_functions.pinecone_helper import upload_chunks_to_pinecone, get_top_k_similar

load_dotenv()
os.environ["GROQ_Key"] = os.getenv("GROQ_API_KEY")



# business_data = ""
# with open("data/rag_data.txt", "r", encoding="utf-8", errors="ignore") as f:
#     business_data = f.read()
#     f.close() # close the file after reading


# system_prompt = ""

# with open("data/system_prompt.txt", "r", encoding="utf-8", errors="ignore") as f:
#     system_prompt = f.read()
#     f.close() # close the file after reading

def get_business_data():
    with open("data/rag_data.txt", "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def get_system_prompt():
    with open("data/system_prompt.txt", "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class State(TypedDict):
    messages: list[BaseMessage]
    response: str  # the response to the query
    context_docs: List[str]  # the context documents
    path: str  # the path to the current state
    history_docs: List[str]  # the history documents
    query: str  # the query from the user
    business_name: str  # the name of the business


class RouteQuery(BaseModel):
    datasource: Literal["vectorstore", "wiki_search", "llm", "exit"] = Field(
        ...,
        description="Route query to appropriate source: 'vectorstore' for RAG , 'wiki_search' for general knowledge, 'llm' for unrelated questions, and 'exit' for quitting.",
    )





def route(state: State):

    # print("Reached Route")

    business_name = state["business_name"]


    # business_data = state["rag_data"]

    business_data = get_business_data()

    llm = ChatGroq(
        groq_api_key=os.environ["GROQ_Key"], model_name="llama-3.3-70b-versatile"
    )

    # Extract keywords from the business name and data
    keywords = llm.invoke(
        f"Extract the most important keywords or topic titles from the business name '{business_name}' and the data '{business_data}' that we used to route the query to the appropriate source. Only return the keywords or topic titles, separated by commas. Do not include any other text or explanation. "
    )
    # remove think from the response
    keywords = keywords.content
    # keywords = keywords.content.split("</think>")[-1].strip()

    # print("Keywords : ", keywords)

    route_prompt = ChatPromptTemplate(
        [
            (
                "system",
                f"""

        You are an AI assistant responsible for routing user queries to the most appropriate source.
        You have access to:
        1. {business_name} Vectorstore - Contains detailed information about {business_name} which includes {keywords}
        2. Wikipedia Search (wiki_search) - Use this for general knowledge questions that are not related to {business_name}.
        3. LLM - Handle all other queries using LLM, including random, open-ended, or unclear questions.
        4. Exit - If the user explicitly states they want to exit (e.g., "exit," "quit," "end chat"), return "exit".

        **Routing Rules:**
        - If the query is about {business_name}, route it to vectorstore.
        - If the query is general factual knowledge, use wiki_search.
        - All other queries, by default, should go to LLM.
        - If the query is about exiting, return "exit".
        Always ensure queries are routed efficiently and accurately.

        Return the response in this format:
        

        """,
            ),
            ("human", "{query}"),
        ]
    )

    # print("Route Prompt : ", route_prompt)
    llm = ChatGroq(
        groq_api_key=os.environ["GROQ_Key"], model_name="llama-3.3-70b-versatile"
    )

    llm = llm.with_structured_output(RouteQuery)

    router = route_prompt | llm

    query = state["messages"][-1].content

    source = router.invoke({"query": query})
    if source.datasource.lower() == "vectorstore":
        return "vectorstore"
    elif source.datasource.lower() == "wiki_search":
        return "wiki_search"

    elif source.datasource.lower() == "llm":
        return "llm"

    elif source.datasource.lower() == "exit":
        return "end"


def retrieve_docs(state: State):
    print("Reached RAG")

    query = state["messages"][-1].content
    namespace = state["business_name"].replace(" ","").lower()
    
    top_k_result = get_top_k_similar(query, namespace, k=3)
    context = top_k_result.split("\n") if top_k_result else []

    # print("fetching RAG context from Pinecone for namespace:", namespace)
    # print("Context : ", context)
    # print("\n\n")


    return {"context_docs": context, "messages": state["messages"]}


api_wrapper = WikipediaAPIWrapper(top_k_result=1, doc_content=500)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)


def wiki_search(state: State):
    print("Reached Wiki")
    docs = wiki.invoke(state["messages"][-1].content)
    return {"context_docs": [docs], "messages": state["messages"]}


def llm_query(state: State):
    print("Reached LLM Query")
    business_name = state["business_name"]
    messages = [
        SystemMessage(
            content=f"You are an Helpful AI assistant designed to assist users with their queries. Your goal is to provide helpful, engaging, and natural responses—just like a real human assistant. Generate your name from the {business_name} and respond to the user query. "
        ),
        HumanMessage(content=state["messages"][-1].content),
    ]

    response = llm.invoke(messages)


    # print("Testing LLM Response : ", response.content )
    # print("\n\n")




    # Extract content from the response
    response_text = response.content.split("</think>")[-1]

    return {"context_docs": [response_text], "messages": state["messages"]}


def history_retriver(state: State):

    bussiness_name = state["business_name"]
    namespace = "history_"+ bussiness_name.replace(" ", "").lower()

    print("Reached History")

    query = state["messages"][-1].content

    llm = ChatGroq(
        groq_api_key=os.environ["GROQ_Key"], model_name="llama-3.3-70b-versatile"
    )
    history_data = ""
    # Add the latest message to the history

    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            history_data += f"User :{message.content.strip()}\n"

        else:
            history_data += f"AI_Bot :{message.content.strip()}\n"

    system_prompt = f"""
    You are a smart summarization assistant. Read the full conversation between the User and AI_Bot, and generate a concise yet complete summary.

    Include:
    - The User's key questions or problems.
    - The AI_Bot's main responses, solutions, or suggestions.
    - Any important technical or informational content.

    Avoid repetition—summarize repeated topics only once. Exclude timestamps or speaker labels. Output a clear, paragraph-style summary that captures all unique points discussed. Given the conversation below:

    {history_data}
    """

    response = llm.invoke(system_prompt)


    fin_response = response.content

    text = ""
    for doc in fin_response.split("\n"):
        if doc.strip():
            text += doc.strip() + "\n\n"
    
    text_splitter= RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", " ", ".",","]
        )


    data_chunks = text_splitter.split_text(text)

    upload_chunks_to_pinecone(data_chunks, namespace)
    # print("History data uploaded to Pinecone for namespace:", namespace)


    top_k_history_result = get_top_k_similar(query,namespace,k=1)
    # print("Fetching history from Pinecone for namespace:", namespace)
    # print("Top K History Result : ", top_k_history_result)
    # print("\n\n")
    history = top_k_history_result.split("\n") if top_k_history_result else []
    return {"history_docs": history, "messages": state["messages"]}

    # test the function


llm = ChatGroq(
    groq_api_key=os.environ["GROQ_Key"],
    model_name="llama-3.3-70b-versatile",
)


def chatbot(state: State):

    print("Reached Chatbot")
    system_prompt = get_system_prompt()


    context = " ".join(state["context_docs"]).join(state["history_docs"])

    full_system_prompt = system_prompt + " " + context
    


    print("Full System Prompt : ", full_system_prompt)
    print("\n\n")

    messages = [
        SystemMessage(content=full_system_prompt),
        # *state["messages"],
    ]

    print("Reached LLM")
    response = llm.invoke(messages)
    response = response.content

    # response = response.content.split("</think>")[-1]
    # print("Response : ", response)
    return {
        "response": str(response),
        "messages": state["messages"] + [AIMessage(content=response)],
    }


# recognizer = sr.Recognizer()
# mic = sr.Microphone()


def speech_to_text(state: State):

    query = state["query"]
    # # print("Query : ", query)
    messages = state.get("messages", [])

    return {"messages": messages + [HumanMessage(content=query)]}


import os


builder = StateGraph(State)
builder.add_node("stt", speech_to_text)
builder.add_node("wiki_search", wiki_search)
builder.add_node("RAG", retrieve_docs)
builder.add_node("llm", llm_query)
builder.add_node("chatbot", chatbot)
# builder.add_node("tts", text_to_speech)

builder.add_node("history", history_retriver)

builder.add_edge(START, "stt")
builder.add_conditional_edges(
    "stt",
    route,
    {
        "wiki_search": "wiki_search",
        "vectorstore": "RAG",
        "llm": "llm",
        "end": END,
    },
)

builder.add_edge("RAG", "history")
builder.add_edge("wiki_search", "history")
builder.add_edge("llm", "history")
builder.add_edge("history", "chatbot")


# builder.add_edge("chatbot", "tts")
# builder.add_edge("tts", "stt")
graph = builder.compile()


# --------------------------------------------




def generate_output(business_name,query):
    config = {"configurable": {"thread_id": "2"}}
    # use query as input for the graph
    response = graph.invoke(
        {
            "business_name": business_name,
            "query": query},
        config=config,
        stream_mode="values",
    )
    return response
