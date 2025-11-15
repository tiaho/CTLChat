"""
Conversation summarization for efficient context management.
Summarizes conversation history to reduce token usage while maintaining context.
"""

import anthropic
from loguru import logger
from config import settings

MESSAGES_PER_SUMMARY = 10  # Summarize every 10 messages (5 user + 5 assistant)


def summarize_messages(messages: list, org_name: str = None) -> str:
    """
    Create a concise summary of a batch of conversation messages.

    Args:
        messages: List of message dicts with 'role' and 'content'
        org_name: Optional organization name for context

    Returns:
        Summary string capturing key points and context
    """
    if not messages:
        return ""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Format messages for summary
    conversation_text = ""
    for msg in messages:
        role = "User" if msg['role'] == 'user' else "Assistant"
        conversation_text += f"{role}: {msg['content']}\n\n"

    org_context = f" for {org_name}" if org_name else ""

    system_prompt = f"""You are a conversation summarizer{org_context}.

Your task is to create a concise summary of a conversation that captures:
1. Main topics discussed
2. Key questions asked by the user
3. Important information provided in answers
4. Any decisions, actions, or follow-ups mentioned
5. Context needed to understand future questions

Keep the summary brief but informative (2-4 sentences).
Focus on what's relevant for understanding follow-up questions.

Example:
Input conversation:
User: What's our PTO policy?
Assistant: Employees get 15 days PTO annually, accrued monthly. You can carry over up to 5 days.
User: How do I request time off?
Assistant: Submit requests through the HR portal at least 2 weeks in advance. Your manager will approve.

Output summary:
Discussed PTO policy (15 days annually, 5 day carryover) and the time-off request process (HR portal, 2 weeks advance notice, manager approval required)."""

    user_message = f"""Summarize this conversation concisely:

{conversation_text}

Provide a brief summary in 2-4 sentences."""

    logger.info(f"📝 Summarizing {len(messages)} messages...")

    try:
        message = client.messages.create(
            model=settings.model_name,
            max_tokens=256,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        summary = message.content[0].text.strip()
        logger.info(f"✅ Summary created: {summary[:100]}...")
        return summary

    except Exception as e:
        logger.warning(f"⚠️ Summarization failed: {e}")
        # Fallback: create a simple summary
        return f"Previous discussion covered {len(messages)} messages about various topics."


def build_conversation_context(messages: list, org_name: str = None) -> dict:
    """
    Build conversation context with smart summarization.

    Strategy:
    - If <= 10 messages: return full history
    - If > 10 messages:
        - Summarize older messages in batches of 10
        - Keep recent unsummarized messages as full text
        - Return: summaries + recent messages

    Args:
        messages: List of all conversation messages (ordered chronologically)
        org_name: Optional organization name for context

    Returns:
        Dict with:
            - summaries: List of summary strings
            - recent_messages: List of recent full messages
            - total_messages: Total message count
            - summarized_count: How many messages were summarized
    """
    if not messages:
        return {
            "summaries": [],
            "recent_messages": [],
            "total_messages": 0,
            "summarized_count": 0
        }

    total_count = len(messages)

    # If conversation is short, return all messages
    if total_count <= MESSAGES_PER_SUMMARY:
        logger.info(f"💬 Conversation has {total_count} messages - using full history")
        return {
            "summaries": [],
            "recent_messages": messages,
            "total_messages": total_count,
            "summarized_count": 0
        }

    # Calculate how many messages to summarize
    # Keep the remainder as recent messages
    num_to_summarize = (total_count // MESSAGES_PER_SUMMARY) * MESSAGES_PER_SUMMARY
    num_recent = total_count - num_to_summarize

    logger.info(f"💬 Conversation has {total_count} messages")
    logger.info(f"   Summarizing: {num_to_summarize} messages")
    logger.info(f"   Keeping recent: {num_recent} messages")

    # Split messages
    messages_to_summarize = messages[:num_to_summarize]
    recent_messages = messages[num_to_summarize:]

    # Create summaries in batches
    summaries = []
    for i in range(0, num_to_summarize, MESSAGES_PER_SUMMARY):
        batch = messages_to_summarize[i:i + MESSAGES_PER_SUMMARY]
        batch_num = (i // MESSAGES_PER_SUMMARY) + 1
        logger.info(f"   Creating summary {batch_num}...")
        summary = summarize_messages(batch, org_name)
        summaries.append(summary)

    return {
        "summaries": summaries,
        "recent_messages": recent_messages,
        "total_messages": total_count,
        "summarized_count": num_to_summarize
    }


def format_context_for_claude(context: dict) -> str:
    """
    Format conversation context into a string for Claude.

    Args:
        context: Output from build_conversation_context()

    Returns:
        Formatted string with summaries and recent messages
    """
    if context["total_messages"] == 0:
        return ""

    parts = []

    # Add summaries if present
    if context["summaries"]:
        parts.append("## Previous Conversation Summary")
        for i, summary in enumerate(context["summaries"], 1):
            parts.append(f"Summary {i}: {summary}")
        parts.append("")  # blank line

    # Add recent messages
    if context["recent_messages"]:
        if context["summaries"]:
            parts.append("## Recent Messages")
        for msg in context["recent_messages"]:
            role = "User" if msg['role'] == 'user' else "Assistant"
            # Truncate very long messages for context
            content = msg['content']
            if len(content) > 500:
                content = content[:500] + "..."
            parts.append(f"{role}: {content}")

    return "\n".join(parts)


def get_conversation_context_string(messages: list, org_name: str = None) -> str:
    """
    Convenience function to get formatted conversation context in one call.

    Args:
        messages: List of all conversation messages
        org_name: Optional organization name

    Returns:
        Formatted conversation context string ready for Claude
    """
    context = build_conversation_context(messages, org_name)
    return format_context_for_claude(context)
