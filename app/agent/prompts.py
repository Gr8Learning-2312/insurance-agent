"""
Prompt templates for the Insurance Claims Agent.
Converted from your SmolAgents prompts.
"""

PARSE_CLAIM_PROMPT = """You are a claims processing assistant. Parse the following claim JSON and extract key information.

Claim JSON:
{claim_json}

Extract and return ONLY a JSON object with these fields:
- claim_id: The claim identifier
- policy_holder: Name of the policy holder
- vendor_name: The service provider/vendor name
- invoice_items: List of items claimed
- claim_amount: Total claim amount

Return ONLY valid JSON, no explanations."""

VALIDATE_CLAIM_PROMPT = """You are a claims validation assistant. Determine if the following claim is valid.

Claim Details:
- Claim ID: {claim_id}
- Policy Holder: {policy_holder}
- Vendor: {vendor_name}
- Amount: ${claim_amount}

A claim is VALID if:
1. All required fields are present
2. Claim amount is greater than 0
3. Vendor name is not empty
4. Policy holder is identified

Return ONLY a JSON object:
{{
  "is_valid": true/false,
  "reason": "explanation if invalid, empty string if valid"
}}"""

GENERATE_POLICY_QUERIES_PROMPT = """You are a policy research assistant. Generate search queries to retrieve relevant policy information.

Claim Details:
- Vendor: {vendor_name}
- Items: {invoice_items}
- Amount: ${claim_amount}

Generate 2-3 specific search queries to find relevant policy sections about:
- Coverage for these types of services
- Vendor requirements
- Claim amount limits

Return ONLY a JSON array of query strings:
["query 1", "query 2", "query 3"]"""

GENERATE_RECOMMENDATION_PROMPT = """You are a claims adjudication assistant. Based on the policy information and claim details, provide a recommendation.

Claim Details:
- Claim ID: {claim_id}
- Vendor: {vendor_name}
- Amount: ${claim_amount}
- Items: {invoice_items}

Relevant Policy Information:
{policy_text}

Analyze the claim against the policy and provide:
1. Recommendation: APPROVE or DENY
2. Reasoning: Detailed explanation

Return ONLY a JSON object:
{{
  "recommendation": "APPROVE/DENY",
  "reasoning": "detailed explanation based on policy"
}}"""

FINALIZE_DECISION_PROMPT = """You are a claims decision assistant. Based on all information, provide the final decision.

Claim ID: {claim_id}
Initial Recommendation: {recommendation}
Recommendation Reasoning: {recommendation_reasoning}
Price Check Result: {price_check_result}

Provide a final decision considering:
1. Policy compliance
2. Price verification results
3. Any red flags

Return ONLY a JSON object:
{{
  "final_decision": "APPROVED/DENIED/REQUIRES_REVIEW",
  "final_reasoning": "comprehensive explanation"
}}"""
