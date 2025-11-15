"""
Query preprocessing using Claude to enhance intent understanding and searchability.
"""

import anthropic
import json
from loguru import logger
from config import settings


def preprocess_query(query: str, org_name: str = None, conversation_context: str = None) -> dict:
    """
    Use Claude to analyze and enhance a user's query before embedding.

    This preprocessing step:
    1. Identifies query intent (facts, procedures, people, policy, etc.)
    2. Rewrites the query to be more searchable
    3. Suggests related organizational terms and jargon
    4. Expands abbreviations and implicit context
    5. Resolves references from conversation history

    Args:
        query: Raw user question
        org_name: Optional organization name for context
        conversation_context: Optional conversation history for resolving references

    Returns:
        Dict containing:
            - original_query: The raw user input
            - intent_type: Categorized intent (facts/procedures/people/policy/general)
            - enhanced_query: Rewritten query optimized for embedding search
            - related_terms: List of related terms and synonyms
            - reasoning: Brief explanation of the enhancement
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    org_context = f" for {org_name}" if org_name else ""

    system_prompt = """You are a query preprocessing expert for organizational knowledge retrieval systems.

Your task is to analyze user queries and optimize them for semantic search against organizational documents.

If conversation history is provided, use it to:
- Resolve pronouns and references (e.g., "they", "that", "it")
- Understand implicit context from previous questions
- Identify the current topic being discussed

For each query, you must:
1. Identify the INTENT TYPE (choose one):
   - facts: Requesting specific factual information (who, what, when, where)
   - procedures: Asking how to do something or about processes/workflows
   - people: Questions about team members, roles, or contacts
   - policy: Questions about rules, guidelines, or official policies
   - general: General questions or exploratory queries

2. REWRITE the query to be more searchable by:
   - Expanding conversational language into key terms
   - Converting questions into declarative keyword phrases
   - Including likely document terminology
   - Adding common organizational jargon variations

3. IDENTIFY related terms that might appear in relevant documents:
   - Synonyms and alternative phrasings
   - Common abbreviations or acronyms
   - Related concepts that might be mentioned together
   - Technical or domain-specific terminology

You must respond with ONLY a valid JSON object in this exact format:
{
  "intent_type": "facts|procedures|people|policy|general",
  "enhanced_query": "rewritten query with key terms",
  "related_terms": ["term1", "term2", "term3"],
  "reasoning": "brief explanation of enhancements made"
}

Examples:

Query: "How do we handle remote work?"
Response:
{
  "intent_type": "policy",
  "enhanced_query": "remote work policy procedure guidelines work from home telecommuting requirements",
  "related_terms": ["WFH", "telecommuting", "flexible work", "distributed team", "home office"],
  "reasoning": "Expanded conversational question into policy-related keywords likely to appear in HR documents"
}

Query: "Who is in charge of marketing?"
Response:
{
  "intent_type": "people",
  "enhanced_query": "marketing department head leader manager director team",
  "related_terms": ["CMO", "marketing lead", "brand manager", "marketing coordinator"],
  "reasoning": "Converted people question into role-based search terms"
}

Query: "What's our PTO policy?"
Response:
{
  "intent_type": "policy",
  "enhanced_query": "PTO paid time off vacation leave policy accrual sick days holiday",
  "related_terms": ["vacation days", "sick leave", "personal days", "time off request", "leave of absence"],
  "reasoning": "Expanded PTO acronym and added related leave terminology"
}"""

    # Build user message with optional conversation context
    user_message_parts = []

    if conversation_context:
        user_message_parts.append(
            f"Conversation History:\n{conversation_context}\n\n---\n")

    user_message_parts.append(f"Analyze and enhance this query{org_context}:")
    user_message_parts.append(f"\nQuery: {query}")
    user_message_parts.append("\nRespond with the JSON object only.")

    user_message = "".join(user_message_parts)

    logger.info(f"🔍 Preprocessing query: '{query}'")

    try:
        message = client.messages.create(
            model=settings.model_name,
            max_tokens=512,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If response isn't valid JSON, extract it from markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                result = json.loads(response_text)
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                result = json.loads(response_text)
            else:
                raise

        # Add original query
        result["original_query"] = query

        logger.info(f"✅ Query enhanced: '{result['enhanced_query']}'")
        logger.info(f"   Intent: {result['intent_type']}")
        logger.info(
            f"   Related terms: {', '.join(result['related_terms'][:3])}...")

        return result

    except Exception as e:
        logger.warning(f"⚠️ Query preprocessing failed: {e}")
        logger.warning("   Using original query as fallback")

        # Fallback to original query if preprocessing fails
        return {
            "original_query": query,
            "intent_type": "general",
            "enhanced_query": query,
            "related_terms": [],
            "reasoning": "Preprocessing failed, using original query"
        }


def build_search_query(preprocessing_result: dict) -> str:
    """
    Build the final search query string from preprocessing results.

    This combines the enhanced query with related terms to create
    a comprehensive search string for embedding.

    Args:
        preprocessing_result: Output from preprocess_query()

    Returns:
        Combined search query string
    """
    enhanced = preprocessing_result["enhanced_query"]
    related = preprocessing_result.get("related_terms", [])

    # Combine enhanced query with top related terms
    # Weight the enhanced query more heavily by mentioning it first
    search_parts = [enhanced]

    # Add related terms (limit to top 5 to avoid dilution)
    if related:
        search_parts.append(" ".join(related[:5]))

    return " ".join(search_parts)
