"""
LangGraph workflow for Insurance Claims Processing.
Converts your SmolAgents workflow to LangGraph state machine.
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.agent.state import ClaimState
from app.agent.tools import (
    parse_claim,
    is_valid_query,
    generate_policy_queries,
    retrieve_policy_text,
    generate_recommendation,
    finalize_decision
)
from app.utils.logger import logger
from app.utils.config import config

# Initialize LLM
llm = ChatOpenAI(
    model=config.model_name,
    api_key=config.openai_api_key,
    base_url=config.openai_base_url,
    temperature=0
)


# === NODE FUNCTIONS ===

def parse_claim_node(state: ClaimState) -> ClaimState:
    """Node 1: Parse incoming claim JSON"""
    logger.info("📍 NODE: parse_claim_node - Starting claim parsing")
    
    result = parse_claim.invoke({"claim_json": state["claim_json"]})
    
    state["claim_id"] = result.get("claim_id")
    state["policy_holder"] = result.get("policy_holder")
    state["vendor_name"] = result.get("vendor_name")
    state["invoice_items"] = result.get("invoice_items")
    state["claim_amount"] = result.get("claim_amount")
    state["current_step"] = "parsed"
    
    return state


def validate_claim_node(state: ClaimState) -> ClaimState:
    """Node 2: Validate claim requirements"""
    logger.info("📍 NODE: validate_claim_node - Validating claim")
    
    claim_data = {
        "claim_id": state["claim_id"],
        "policy_holder": state["policy_holder"],
        "vendor_name": state["vendor_name"],
        "claim_amount": state["claim_amount"]
    }
    
    result = is_valid_query.invoke({"claim_data": claim_data})
    
    state["is_valid"] = result.get("is_valid", False)
    state["validation_reason"] = result.get("reason", "")
    state["current_step"] = "validated"
    
    return state


def generate_queries_node(state: ClaimState) -> ClaimState:
    """Node 3: Generate policy search queries"""
    logger.info("📍 NODE: generate_queries_node - Generating search queries")
    
    claim_data = {
        "vendor_name": state["vendor_name"],
        "invoice_items": state["invoice_items"],
        "claim_amount": state["claim_amount"]
    }
    
    queries = generate_policy_queries.invoke({"claim_data": claim_data})
    
    state["policy_queries"] = queries
    state["current_step"] = "queries_generated"
    
    return state


def retrieve_policy_node(state: ClaimState) -> ClaimState:
    """Node 4: Retrieve relevant policy text"""
    logger.info("📍 NODE: retrieve_policy_node - Retrieving policy information")
    
    policy_text = retrieve_policy_text.invoke({"queries": state["policy_queries"]})
    
    state["retrieved_policy_text"] = policy_text
    state["current_step"] = "policy_retrieved"
    
    return state


def recommendation_node(state: ClaimState) -> ClaimState:
    """Node 5: Generate recommendation"""
    logger.info("📍 NODE: recommendation_node - Generating recommendation")
    
    claim_data = {
        "claim_id": state["claim_id"],
        "vendor_name": state["vendor_name"],
        "claim_amount": state["claim_amount"],
        "invoice_items": state["invoice_items"]
    }
    
    result = generate_recommendation.invoke({
        "claim_data": claim_data,
        "policy_text": state["retrieved_policy_text"]
    })
    
    state["recommendation"] = result.get("recommendation")
    state["recommendation_reasoning"] = result.get("reasoning")
    state["current_step"] = "recommendation_generated"
    
    return state


def price_check_node(state: ClaimState) -> ClaimState:
    """Node 6: Check for price inflation (simplified)"""
    logger.info("📍 NODE: price_check_node - Checking prices")
    
    # Simplified price check logic
    # In production, this would call external pricing APIs
    claim_amount = state["claim_amount"] or 0
    
    if claim_amount > 10000:
        state["price_check_result"] = "HIGH_AMOUNT_FLAGGED"
        logger.warning(f"⚠️ High claim amount: ${claim_amount}")
    else:
        state["price_check_result"] = "WITHIN_NORMAL_RANGE"
        logger.info(f"✅ Claim amount acceptable: ${claim_amount}")
    
    state["current_step"] = "price_checked"
    
    return state


def finalize_decision_node(state: ClaimState) -> ClaimState:
    """Node 7: Make final decision"""
    logger.info("📍 NODE: finalize_decision_node - Finalizing decision")
    
    claim_data = {
        "claim_id": state["claim_id"]
    }
    
    result = finalize_decision.invoke({
        "claim_data": claim_data,
        "recommendation": state["recommendation"],
        "recommendation_reasoning": state["recommendation_reasoning"],
        "price_check_result": state["price_check_result"]
    })
    
    state["final_decision"] = result.get("final_decision")
    state["final_reasoning"] = result.get("final_reasoning")
    state["current_step"] = "completed"
    
    return state


def invalid_claim_node(state: ClaimState) -> ClaimState:
    """Terminal node for invalid claims"""
    logger.info("📍 NODE: invalid_claim_node - Claim rejected as invalid")
    
    state["final_decision"] = "INVALID"
    state["final_reasoning"] = state["validation_reason"]
    state["current_step"] = "completed"
    
    return state


# === CONDITIONAL EDGES ===

def should_continue_after_validation(state: ClaimState) -> Literal["continue", "invalid"]:
    """Decide whether to continue or reject based on validation"""
    if state["is_valid"]:
        logger.info("✅ Routing to policy retrieval (claim is valid)")
        return "continue"
    else:
        logger.warning("⚠️ Routing to rejection (claim is invalid)")
        return "invalid"


# === BUILD GRAPH ===

def create_claims_processing_graph():
    """Create and compile the LangGraph workflow"""
    logger.info("🏗️ Building LangGraph workflow")
    
    workflow = StateGraph(ClaimState)
    
    # Add nodes
    workflow.add_node("parse_claim", parse_claim_node)
    workflow.add_node("validate_claim", validate_claim_node)
    workflow.add_node("generate_queries", generate_queries_node)
    workflow.add_node("retrieve_policy", retrieve_policy_node)
    workflow.add_node("recommendation", recommendation_node)
    workflow.add_node("price_check", price_check_node)
    workflow.add_node("finalize_decision", finalize_decision_node)
    workflow.add_node("invalid_claim", invalid_claim_node)
    
    # Set entry point
    workflow.set_entry_point("parse_claim")
    
    # Add edges
    workflow.add_edge("parse_claim", "validate_claim")
    
    # Conditional edge after validation
    workflow.add_conditional_edges(
        "validate_claim",
        should_continue_after_validation,
        {
            "continue": "generate_queries",
            "invalid": "invalid_claim"
        }
    )
    
    workflow.add_edge("generate_queries", "retrieve_policy")
    workflow.add_edge("retrieve_policy", "recommendation")
    workflow.add_edge("recommendation", "price_check")
    workflow.add_edge("price_check", "finalize_decision")
    workflow.add_edge("finalize_decision", END)
    workflow.add_edge("invalid_claim", END)
    
    # Compile
    app = workflow.compile()
    
    logger.info("✅ LangGraph workflow compiled successfully")
    return app


# Create global graph instance
claims_graph = create_claims_processing_graph()

# Save the workflow as a PNG for visualization
png_bytes = claims_graph.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(png_bytes)



