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

# 1. DEFINE THE STATE (Updated to include risk_score)
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    project_idea: str
    plan: str
    review_feedback: str
    risk_score: str  # New field for Risk Analysis

# 2. INITIALIZE LLM 
# Note: Using gemini-1.5-flash for current stability
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))

# 3. DEFINE THE NODES
def planner_node(state: AgentState):
    prompt = f"As a Lead Data Scientist, create a test plan for: {state['project_idea']}"
    response = llm.invoke([SystemMessage(content="Create a detailed technical plan."), HumanMessage(content=prompt)])
    return {"plan": response.content, "messages": [response]}

def reviewer_node(state: AgentState):
    prompt = f"Review this plan for missing tools or unrealistic timelines: {state['plan']}"
    response = llm.invoke([SystemMessage(content="Be critical. Find 2 improvements."), HumanMessage(content=prompt)])
    return {"review_feedback": response.content, "messages": [response]}

# NEW NODE: Risk Analyst
def risk_analyst_node(state: AgentState):
    prompt = f"""
    Analyze the following Data Science project for risks: {state['project_idea']}
    Provide a concise report covering:
    1. Technical Risk (e.g., potential for overfitting or data leakage).
    2. Business Risk (e.g., operational impact if the model fails).
    3. Final Risk Score (Low, Medium, or High).
    """
    response = llm.invoke([SystemMessage(content="You are a Senior Risk Management Consultant."), HumanMessage(content=prompt)])
    return {"risk_score": response.content, "messages": [response]}

# 4. BUILD THE GRAPH
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("risk_analyst", risk_analyst_node) # Added Node

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "reviewer")
workflow.add_edge("reviewer", "risk_analyst") # Flow goes from Reviewer to Risk Analyst
workflow.add_edge("risk_analyst", END)

app = workflow.compile(checkpointer=MemorySaver())

# 5. STREAMLIT UI
st.set_page_config(page_title="AI Test Pilot", page_icon="✈️", layout="wide")
st.title("🤖 Advanced DS Test Pilot Agent")
st.markdown("### Agentic QA & Risk Assessment Workflow")

user_input = st.text_input("Describe your DS project:", placeholder="e.g. Airline Cargo Delay Prediction")

if st.button("Generate Advanced Plan"):
    if user_input:
        with st.spinner("Multi-agent system analyzing project..."):
            config = {"configurable": {"thread_id": "streamlit_demo"}}
            final_state = app.invoke({"project_idea": user_input, "messages": []}, config)
            
            st.success("Analysis Complete!")
            
            # Layout with two columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Final Optimized Plan")
                st.markdown(final_state["plan"])
            
            with col2:
                st.subheader("⚠️ Risk Assessment")
                st.warning(final_state["risk_score"])
                
                with st.expander("🔍 See Peer Review Feedback"):
                    st.write(final_state["review_feedback"])
    else:
        st.warning("Please enter a project description first.")