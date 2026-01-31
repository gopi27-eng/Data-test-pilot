import streamlit as st
import operator
import os 
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

load_dotenv()
# 1. DEFINE THE STATE
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    project_idea: str
    plan: str
    review_feedback: str

# 2. INITIALIZE LLM (Use your actual key here)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))

# 3. DEFINE THE NODES
def planner_node(state: AgentState):
    prompt = f"As a Lead Data Scientist, create a test plan for: {state['project_idea']}"
    response = llm.invoke([SystemMessage(content="Create a detailed technical plan."), HumanMessage(content=prompt)])
    return {"plan": response.content, "messages": [response]}

def reviewer_node(state: AgentState):
    prompt = f"Review this plan for missing tools or unrealistic timelines: {state['plan']}"
    response = llm.invoke([SystemMessage(content="Be critical. Find 2 improvements."), HumanMessage(content=prompt)])
    return {"review_feedback": response.content, "messages": [response]}

# 4. BUILD THE GRAPH (This creates the 'app' variable)
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "reviewer")
workflow.add_edge("reviewer", END)

# This is the line that was missing or disconnected:
app = workflow.compile(checkpointer=MemorySaver())

# 5. STREAMLIT UI
st.set_page_config(page_title="AI Test Pilot", page_icon="✈️")
st.title("Advanced DS Test Pilot Agent")
st.info("Agentic Workflow for EPAM Interview Preparation")

user_input = st.text_input("Describe your DS project:", placeholder="e.g. Airline Cargo Delay Prediction")

if st.button("Generate Advanced Plan"):
    if user_input:
        with st.spinner("Agent is thinking..."):
            # We use a thread_id to keep the memory consistent
            config = {"configurable": {"thread_id": "streamlit_demo"}}
            final_state = app.invoke({"project_idea": user_input, "messages": []}, config)
            
            st.success("Analysis Complete!")
            st.subheader("📋 Final Optimized Plan")
            st.markdown(final_state["plan"])
            
            with st.expander("🔍 See Agent's Internal Review"):
                st.write(final_state["review_feedback"])
    else:
        st.warning("Please enter a project description first.")