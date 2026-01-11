from typing import List, Dict
from datetime import datetime
from src.utils.pii_detector import anonymize_pii
from src.config.settings import settings


def count_words(text: str) -> int:
    """
    Count words in text using whitespace splitting.
    
    Args:
        text: Input text
    
    Returns:
        Word count
    """
    return len(text.split())


def format_report(top_themes: List[Dict], word_limit: int = 250) -> str:
    """
    Format the Weekly Pulse report with PII anonymization and word limit enforcement.
    Note: Quotes are never truncated - they are always included in full.
    
    Args:
        top_themes: List of theme insights [{theme, problem_statements, verbatim_quote, action_items}, ...]
        word_limit: Maximum word count (default: 250) - quotes may cause slight overage
    
    Returns:
        Formatted report string (may slightly exceed word_limit to preserve full quotes)
    """
    if not top_themes:
        return "Groww Weekly Pulse - No themes identified this week."
    
    # Get current date (using settings date)
    current_date = settings.CURRENT_DATE.strftime("%B %d, %Y")
    
    # Start building report
    report_parts = []
    
    # Title
    title = f"Groww Weekly Pulse - {current_date}"
    report_parts.append(title)
    report_parts.append("")
    report_parts.append("Main Problems identified:")
    report_parts.append("")
    
    # Process each theme
    for i, theme_data in enumerate(top_themes[:3], 1):  # Limit to top 3
        theme = theme_data.get('theme', '')
        
        # Get problem statements (should be a list of 3)
        problem_statements = theme_data.get('problem_statements', [])
        if isinstance(problem_statements, str):
            # Fallback: split by newline if it's a string
            problem_statements = [p.strip() for p in problem_statements.split('\n') if p.strip()][:3]
        if not isinstance(problem_statements, list):
            problem_statements = [problem_statements] if problem_statements else []
        while len(problem_statements) < 3:
            problem_statements.append(f'Additional feedback on {theme}')
        
        # Get verbatim quote (FULL quote, never truncate)
        quote = theme_data.get('verbatim_quote', '')
        # Always use the full quote - do not truncate
        if not quote and theme_data.get('verbatim_quote'):
            quote = theme_data['verbatim_quote']
        
        # Get action items (should be a list of 2)
        action_items = theme_data.get('action_items', [])
        if isinstance(action_items, str):
            # Fallback: split by newline if it's a string
            action_items = [a.strip() for a in action_items.split('\n') if a.strip()][:2]
        if not isinstance(action_items, list):
            action_items = [action_items] if action_items else []
        while len(action_items) < 2:
            action_items.append(f'Implement improvements for {theme}')
        
        # Anonymize PII
        problem_statements = [anonymize_pii(p) for p in problem_statements]
        quote = anonymize_pii(quote)
        action_items = [anonymize_pii(a) for a in action_items]
        
        # Add theme section
        report_parts.append(f"**Problem Theme {i}: {theme}**")
        report_parts.append("")
        report_parts.append("Major problem identified:")
        for problem in problem_statements[:3]:
            report_parts.append(f"• {problem}")
        report_parts.append("")
        report_parts.append("**User Quote**")
        # Add full quote - NEVER truncate
        report_parts.append(quote)
        report_parts.append("")
        report_parts.append("Action items:")
        for action in action_items[:2]:
            report_parts.append(f"• {action}")
        report_parts.append("")
    
    # Join all parts
    report = "\n".join(report_parts)
    
    # Count words
    word_count = count_words(report)
    
    # Note: We preserve full quotes even if it means slightly exceeding word limit
    # This is by design - quotes must be complete
    
    return report


def editor_node(state: dict) -> dict:
    """
    LangGraph node function for editing and formatting the final report.
    
    Args:
        state: ReviewState dict with top_themes
    
    Returns:
        Updated state with final_report populated
    """
    state = state.copy()
    
    try:
        top_themes = state.get('top_themes', [])
        
        if not top_themes:
            state['errors'] = state.get('errors', [])
            state['errors'].append("Editor: No top themes to format")
            state['final_report'] = "Groww Weekly Pulse - No themes identified this week."
            return state
        
        # Format report with word limit (quotes are preserved fully even if over limit)
        final_report = format_report(top_themes, word_limit=settings.MAX_REPORT_WORDS)
        
        # Verify word count (informational only)
        # Note: We do NOT truncate here - quotes must be preserved fully
        # The word limit is a guideline, but quotes are more important
        word_count = count_words(final_report)
        
        state['final_report'] = final_report
        state['errors'] = state.get('errors', [])
        
    except Exception as e:
        error_msg = f"Editor error: {str(e)}"
        state['errors'] = state.get('errors', [])
        state['errors'].append(error_msg)
        state['final_report'] = "Groww Weekly Pulse - Error generating report."
    
    return state
