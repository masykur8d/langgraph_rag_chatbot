import asyncio
from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from nicegui import ui, binding

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import END, StateGraph, MessagesState
from langchain_openai import ChatOpenAI

from components.vector_db import get_vector_store

# Create a ZoneInfo object for Japan Standard Time
japan_tz = ZoneInfo("Asia/Tokyo")

class State:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, top_p=0.1)

    def __init__(
            self, shop_name : str, 
            vector_db_namespace : str,
            openai_chat_prompt : str, 
            openai_speech_prompt : str,
            player_pop_up: ui.refreshable,
        ) -> None:
        self.shop_name = shop_name
        self.openai_chat_prompt = openai_chat_prompt
        self.openai_speech_prompt = openai_speech_prompt

        self.vector_db_object = get_vector_store(namespace = vector_db_namespace)
        
        self.memory = MemorySaver()
        self.memory_config = {"configurable": {"thread_id": str(uuid4())}}

        self.last_text_from_speech = ''
        self.is_recording =  False

        self.player_pop_up = player_pop_up

        @tool(response_format="content_and_artifact")
        async def retrieve(query: str):
            """Retrieve information related to a query."""
            retrieved_docs = await self.vector_db_object.asimilarity_search(query=query, k=10)
            serialized = "\n\n".join(
                f"Source: {doc.metadata}\nContent: {doc.page_content}"
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs
        
        self.retrieve = retrieve


    async def initialize(self):
        self.graph = await self.build_graph()
    

    def toggle_recording_status(self):
        self.is_recording = not self.is_recording


    async def get_current_conversation(self, app):
        state = await app.aget_state(self.memory_config).values
        serialized = "\n\n".join(message for message in state["messages"])

        return serialized


    # Generate an AIMessage that may include a tool-call to be sent.
    async def query_or_respond(self, state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_tools = self.llm.bind_tools([self.retrieve])
        response = await llm_with_tools.ainvoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}


    # Generate a response using the retrieved content.
    async def generate(self, state: MessagesState):
        """Generate answer."""
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)

        # Prompt
        system_message_content = f"""
        {self.openai_chat_prompt}
        {docs_content}
        """

        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run
        response = await self.llm.ainvoke(prompt)
        return {"messages": [response]}
    

    async def build_graph(self):
        # Execute the retrieval.
        tools = ToolNode([self.retrieve])

        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node(self.query_or_respond)
        graph_builder.add_node(tools)
        graph_builder.add_node(self.generate)

        graph_builder.set_entry_point("query_or_respond")
        graph_builder.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {END: END, "tools": "tools"},
        )
        graph_builder.add_edge("tools", "generate")
        graph_builder.add_edge("generate", END)

        graph = graph_builder.compile(checkpointer=self.memory)

        return graph
    
    def get_time_stamp(self) -> str:
        # Get the current time in Japan
        now_in_japan = datetime.now(japan_tz)
        time_str = now_in_japan.strftime("%H:%M")
        
        return time_str

    async def stream_manual_message(self, message : str):
        for i in message:
            yield i
            await asyncio.sleep(0.06)