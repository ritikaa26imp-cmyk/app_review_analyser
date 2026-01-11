from typing import TypedDict, List, Dict, Optional


class ReviewState(TypedDict):
    """Shared state for the LangGraph workflow"""
    raw_reviews: List[Dict]  # Output from Extractor: [{rating, date, text}, ...]
    classified_reviews: List[Dict]  # Output from Classifier: [{rating, date, text, theme}, ...]
    top_themes: List[Dict]  # Output from Strategist: [{theme, problem_statement, verbatim_quote, action_idea}, ...]
    final_report: str  # Output from Editor: formatted report ≤250 words
    errors: List[str]  # Error tracking across agents

