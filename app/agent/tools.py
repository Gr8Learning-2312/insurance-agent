"""
LangChain tools converted from your SmolAgents tools.
Maps 1:1 with your existing workflow.
"""
import json
import re
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.utils.logger import logger
from app.utils.config import config
from app.database.vector_store import policy_store
from app.agent.prompts import (
    PARSE_CLAIM_PROMPT,
    VALIDATE_CLAIM_PROMPT,
    GENERATE_POLICY_QUERIES_PROMPT,
    GENERATE_RECOMMENDATION_PROMPT,
    FINALIZE_DECISION_PROMPT
)

# Initialize LLM
llm = ChatOpenAI(
    model=config.model_name,
    api_key=config.openai_api_key,
    base_url=config.openai_base_url,
    temperature=0
)

def extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response that might contain markdown or extra text"""
    try:
        # Try direct JSON parse first
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find JSON object/array in text
        json_match = re.search(r'(\{.*?\}|\[.*?\])', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        raise ValueError(f"Could not extract JSON from: {text}")


@tool
def parse_claim(claim_json: str) -> Dict[str, Any]:
    """
    Parse incoming claim JSON and extract key information.
    
    Args:
        claim_json: Raw claim data as JSON string
    
    Returns:
        Parsed claim data with claim_id, policy_holder, vendor_name, invoice_items, claim_amount
    """
    logger.info(f"🔧 TOOL: parse_claim - Processing claim")
    
    try:
        prompt = PARSE_CLAIM_PROMPT.format(claim_json=claim_json)
        response = llm.invoke(prompt)
        parsed_data = extract_json(response.content)
        
        logger.info(f"✅ Parsed claim ID: {parsed_data.get('claim_id', 'N/A')}")
        return parsed_data
    
    except Exception as e:
        logger.error(f"❌ Error parsing claim: {e}")
        return {"error": str(e)}


@tool
def is_valid_query(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate if the claim meets basic requirements.
    
    Args:
        claim_data: Parsed claim data
    
    Returns:
        {"is_valid": bool, "reason": str}
    """
    logger.info(f"🔧 TOOL: is_valid_query - Validating claim")
    
    try:
        prompt = VALIDATE_CLAIM_PROMPT.format(
            claim_id=claim_data.get("claim_id", "N/A"),
            policy_holder=claim_data.get("policy_holder", "N/A"),
            vendor_name=claim_data.get("vendor_name", "N/A"),
            claim_amount=claim_data.get("claim_amount", 0)
        )
        
        response = llm.invoke(prompt)
        validation_result = extract_json(response.content)
        
        is_valid = validation_result.get("is_valid", False)
        reason = validation_result.get("reason", "")
        
        if is_valid:
            logger.info("✅ Claim is VALID")
        else:
            logger.warning(f"⚠️ Claim is INVALID: {reason}")
        
        return validation_result
    
    except Exception as e:
        logger.error(f"❌ Error validating claim: {e}")
        return {"is_valid": False, "reason": f"Validation error: {str(e)}"}


@tool
def generate_policy_queries(claim_data: Dict[str, Any]) -> List[str]:
    """
    Generate search queries to retrieve relevant policy information.
    
    Args:
        claim_data: Parsed claim data
    
    Returns:
        List of search query strings
    """
    logger.info(f"🔧 TOOL: generate_policy_queries - Creating search queries")
    
    try:
        prompt = GENERATE_POLICY_QUERIES_PROMPT.format(
            vendor_name=claim_data.get("vendor_name", "N/A"),
            invoice_items=json.dumps(claim_data.get("invoice_items", [])),
            claim_amount=claim_data.get("claim_amount", 0)
        )
        
        response = llm.invoke(prompt)
        queries = extract_json(response.content)
        
        if isinstance(queries, dict):
            queries = queries.get("queries", [])
        
        logger.info(f"✅ Generated {len(queries)} policy queries")
        for i, q in enumerate(queries, 1):
            logger.info(f"   Query {i}: {q}")
        
        return queries
    
    except Exception as e:
        logger.error(f"❌ Error generating queries: {e}")
        return []


@tool
def retrieve_policy_text(queries: List[str]) -> str:
    """
    Retrieve relevant policy text from vector store using generated queries.
    
    Args:
        queries: List of search queries
    
    Returns:
        Combined relevant policy text
    """
    logger.info(f"🔧 TOOL: retrieve_policy_text - Retrieving from vector store")
    
    try:
        all_results = []
        
        for query in queries:
            logger.info(f"   Searching for: {query[:60]}...")
            result = policy_store.retrieve(query, top_k=3)
            if result:
                all_results.append(result)
        
        combined_text = "\n\n---\n\n".join(all_results)
        
        logger.info(f"✅ Retrieved {len(combined_text)} characters of policy text")
        return combined_text
    
    except Exception as e:
        logger.error(f"❌ Error retrieving policy text: {e}")
        return ""


@tool
def generate_recommendation(claim_data: Dict[str, Any], policy_text: str) -> Dict[str, Any]:
    """
    Generate claim approval/denial recommendation based on policy.
    
    Args:
        claim_data: Parsed claim data
        policy_text: Retrieved policy information
    
    Returns:
        {"recommendation": str, "reasoning": str}
    """
    logger.info(f"🔧 TOOL: generate_recommendation - Analyzing claim")
    
    try:
        prompt = GENERATE_RECOMMENDATION_PROMPT.format(
            claim_id=claim_data.get("claim_id", "N/A"),
            vendor_name=claim_data.get("vendor_name", "N/A"),
            claim_amount=claim_data.get("claim_amount", 0),
            invoice_items=json.dumps(claim_data.get("invoice_items", [])),
            policy_text=policy_text[:2000]  # Limit context size
        )
        
        response = llm.invoke(prompt)
        recommendation = extract_json(response.content)
        
        rec_decision = recommendation.get("recommendation", "UNKNOWN")
        logger.info(f"✅ Recommendation: {rec_decision}")
        
        return recommendation
    
    except Exception as e:
        logger.error(f"❌ Error generating recommendation: {e}")
        return {"recommendation": "ERROR", "reasoning": str(e)}


@tool
def finalize_decision(
    claim_data: Dict[str, Any],
    recommendation: str,
    recommendation_reasoning: str,
    price_check_result: str
) -> Dict[str, Any]:
    """
    Finalize the claim decision considering all factors.
    
    Args:
        claim_data: Parsed claim data
        recommendation: Initial recommendation
        recommendation_reasoning: Reasoning for recommendation
        price_check_result: Result of price verification
    
    Returns:
        {"final_decision": str, "final_reasoning": str}
    """
    logger.info(f"🔧 TOOL: finalize_decision - Making final decision")
    
    try:
        prompt = FINALIZE_DECISION_PROMPT.format(
            claim_id=claim_data.get("claim_id", "N/A"),
            recommendation=recommendation,
            recommendation_reasoning=recommendation_reasoning,
            price_check_result=price_check_result
        )
        
        response = llm.invoke(prompt)
        final_decision = extract_json(response.content)
        
        decision = final_decision.get("final_decision", "UNKNOWN")
        logger.info(f"✅ FINAL DECISION: {decision}")
        
        return final_decision
    
    except Exception as e:
        logger.error(f"❌ Error finalizing decision: {e}")
        return {"final_decision": "ERROR", "final_reasoning": str(e)}
