from langgraph.graph import StateGraph, END
from src.graph.state import ReviewState
from src.agents.extractor import extract_node
from src.agents.classifier import classify_node
from src.agents.strategist import strategist_node
from src.agents.editor import editor_node


def create_workflow():
    """
    Create and return the LangGraph workflow for the multi-agent system.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Create StateGraph with ReviewState
    workflow = StateGraph(ReviewState)
    
    # Add nodes (agents)
    workflow.add_node("extract", extract_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("editor", editor_node)
    
    # Define the flow: extract → classify → strategist → editor → END
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "classify")
    workflow.add_edge("classify", "strategist")
    workflow.add_edge("strategist", "editor")
    workflow.add_edge("editor", END)
    
    # Compile the workflow
    app = workflow.compile()
    
    return app


# Create workflow instance
workflow_app = create_workflow()

