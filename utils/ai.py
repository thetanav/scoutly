from .models import ScrapedContent, DeepResearchResult
from typing import List
import os
from pydantic_ai import Agent


# Agents with different models
summarizer_agent = Agent(
    'openai:llama3.2',
    system_prompt="You are a summarizer. Summarize the provided content concisely."
)

analyzer_agent = Agent(
    'google-gla:gemini-1.5-flash',
    system_prompt="You are an analyzer. Analyze the query and content to provide deep insights."
)

insight_agent = Agent(
    'openrouter:meta-llama/llama-3.2-3b-instruct:free',
    system_prompt="You are an insight generator. Generate key insights from the content."
)


async def summarize_content(contents: List[ScrapedContent]) -> str:
    """Summarize content using AI agent."""
    combined = " ".join([content.content for content in contents])
    if not combined:
        return "No content to summarize."
    try:
        result = await summarizer_agent.run(f"Summarize this content: {combined[:2000]}")
        return result.data
    except Exception as e:
        return f"Summary failed: {str(e)}"


async def analyze_query(query: str, contents: List[ScrapedContent], model_choice: str = "Ollama (Local)") -> DeepResearchResult:
    """Analyze the query with scraped contents using AI agents."""
    # Select agent based on model_choice
    if model_choice == "Gemini Flash":
        agent = analyzer_agent
    elif model_choice == "OpenRouter (Free)":
        agent = insight_agent
    else:  # Ollama
        agent = summarizer_agent

    summary = await summarize_content(contents)
    # Additional analysis
    combined = " ".join([content.content for content in contents])
    try:
        insights = await agent.run(f"Analyze the query '{query}' and generate insights from this content: {combined[:2000]}")
        analysis = insights.data
    except Exception as e:
        analysis = f"Analysis failed: {str(e)}"

    return DeepResearchResult(
        query=query,
        search_results=[],  # Will be filled elsewhere
        scraped_contents=contents,
        summary=summary,
        analysis=analysis
    )