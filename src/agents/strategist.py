import json
from typing import List, Dict
from collections import Counter
from langchain_groq import ChatGroq
from src.config.settings import settings


# Initialize Groq LLM
def get_llm():
    """Initialize and return Groq LLM client for Strategist Agent"""
    return ChatGroq(
        model="llama-3.1-8b-instant",  # Fast and efficient model
        groq_api_key=settings.GROQ_API_KEY_STRATEGIST,
        temperature=0.3  # Slightly higher temperature for creative insights
    )


def count_reviews_by_theme(classified_reviews: List[Dict]) -> Dict[str, int]:
    """
    Count reviews per theme.
    
    Args:
        classified_reviews: List of classified reviews with theme field
    
    Returns:
        Dictionary mapping theme names to review counts
    """
    theme_counts = Counter()
    for review in classified_reviews:
        theme = review.get('theme', 'Overall Usability')
        theme_counts[theme] += 1
    return dict(theme_counts)


def identify_top_themes(classified_reviews: List[Dict], top_n: int = 3) -> List[str]:
    """
    Identify top N themes by volume (and optionally by severity).
    
    Args:
        classified_reviews: List of classified reviews with theme and rating fields
        top_n: Number of top themes to return
    
    Returns:
        List of top theme names (ordered by volume, then by negative sentiment)
    """
    # Count reviews per theme
    theme_counts = count_reviews_by_theme(classified_reviews)
    
    if not theme_counts:
        return []
    
    # Calculate average rating per theme (lower rating = more negative sentiment)
    theme_ratings = {}
    theme_review_counts = {}
    
    for review in classified_reviews:
        theme = review.get('theme', 'Overall Usability')
        rating = review.get('rating', 3)
        
        if theme not in theme_ratings:
            theme_ratings[theme] = []
            theme_review_counts[theme] = 0
        
        theme_ratings[theme].append(rating)
        theme_review_counts[theme] += 1
    
    # Calculate average rating per theme
    theme_avg_ratings = {}
    for theme, ratings in theme_ratings.items():
        theme_avg_ratings[theme] = sum(ratings) / len(ratings)
    
    # Sort themes by: 1) Volume (count), 2) Severity (lower avg rating = more negative)
    # Priority: Higher volume and lower average rating
    sorted_themes = sorted(
        theme_counts.items(),
        key=lambda x: (x[1], -theme_avg_ratings.get(x[0], 3)),  # Negative for lower rating priority
        reverse=True
    )
    
    # Return top N theme names
    top_themes = [theme for theme, count in sorted_themes[:top_n]]
    
    return top_themes


def generate_insights_for_theme(theme: str, theme_reviews: List[Dict], llm) -> Dict:
    """
    Generate insights (problem statement, verbatim quote, action idea) for a theme.
    
    Args:
        theme: Theme name
        theme_reviews: List of reviews for this theme
        llm: Gemini LLM instance
    
    Returns:
        Dict with theme, problem_statement, verbatim_quote, action_idea
    """
    # Prepare reviews text for LLM (limit to avoid token limits)
    reviews_sample = theme_reviews[:10]  # Use up to 10 reviews for context
    
    reviews_text = ""
    for i, review in enumerate(reviews_sample, 1):
        rating = review.get('rating', 0)
        text = review.get('text', '')
        reviews_text += f"Review {i} (Rating: {rating}/5): {text}\n\n"
    
    prompt = f"""You are a Product Strategist analyzing user reviews for the Groww investment app.

**Theme**: {theme}

**Reviews for this theme**:
{reviews_text}

**Task**: Generate actionable insights for this theme. You must:

1. **Problem Statement**: Write a specific, concise problem statement (1-2 sentences) that captures the core issue or opportunity for this theme based on the reviews.

2. **Verbatim Quote**: Select ONE exact quote from the reviews above (copy it word-for-word, no modifications). This quote should best represent the problem or feedback for this theme. IMPORTANT: The quote must be 100% verbatim - copy it exactly as written in the reviews.

3. **Action Idea**: Propose a specific, technical action idea to address the problem. This must be product-specific to Groww (e.g., "Add stop-loss UI in delivery trades tab", "Implement OTP auto-read for UPI transactions", etc.). Do not suggest generic solutions.

**Output Format** (JSON only):
{{
    "problem_statement": "Your problem statement here",
    "verbatim_quote": "Exact quote from reviews (copy verbatim)",
    "action_idea": "Specific technical action for Groww"
}}

Return ONLY valid JSON, no explanations or markdown formatting.
"""
    
    try:
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Extract JSON from response (handle markdown code blocks if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        insights = json.loads(response_text)
        
        # Ensure verbatim quote is actually from reviews
        verbatim_quote = insights.get('verbatim_quote', '')
        if verbatim_quote:
            # Verify quote exists in reviews (allowing for slight variations)
            quote_found = False
            for review in theme_reviews:
                review_text = review.get('text', '')
                # Check if quote is a substring of any review
                if verbatim_quote.lower() in review_text.lower() or review_text.lower() in verbatim_quote.lower():
                    quote_found = True
                    # Use the exact quote from the review if it's close
                    if len(verbatim_quote) < len(review_text):
                        # Try to find the exact substring
                        idx = review_text.lower().find(verbatim_quote.lower())
                        if idx >= 0:
                            # Extract context around the quote
                            start = max(0, idx - 20)
                            end = min(len(review_text), idx + len(verbatim_quote) + 20)
                            verbatim_quote = review_text[start:end].strip()
                    break
            
            if not quote_found:
                # Fallback: use a quote from the reviews
                for review in theme_reviews:
                    text = review.get('text', '')
                    if len(text) > 50:  # Use a substantial quote
                        verbatim_quote = text[:200] + '...' if len(text) > 200 else text
                        break
        
        return {
            'theme': theme,
            'problem_statement': insights.get('problem_statement', ''),
            'verbatim_quote': verbatim_quote,
            'action_idea': insights.get('action_idea', '')
        }
    
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        # Fallback: create basic insights
        return {
            'theme': theme,
            'problem_statement': f'User feedback on {theme}',
            'verbatim_quote': theme_reviews[0].get('text', '')[:200] if theme_reviews else '',
            'action_idea': f'Review and improve {theme} based on user feedback'
        }
    except Exception as e:
        print(f"Error generating insights for theme {theme}: {e}")
        # Fallback
        return {
            'theme': theme,
            'problem_statement': f'User feedback on {theme}',
            'verbatim_quote': theme_reviews[0].get('text', '')[:200] if theme_reviews else '',
            'action_idea': f'Review and improve {theme} based on user feedback'
        }


def generate_top_themes_insights(classified_reviews: List[Dict], top_n: int = 3) -> List[Dict]:
    """
    Generate insights for top N themes in a single API call.
    
    Args:
        classified_reviews: List of classified reviews with theme field
        top_n: Number of top themes to analyze
    
    Returns:
        List of insight dicts: [{theme, problem_statement, verbatim_quote, action_idea}, ...]
    """
    if not classified_reviews:
        return []
    
    # Identify top themes
    top_themes = identify_top_themes(classified_reviews, top_n=top_n)
    
    if not top_themes:
        return []
    
    print(f"Top {len(top_themes)} themes identified: {', '.join(top_themes)}")
    print("Generating insights for all themes in one API call...")
    
    # Initialize LLM
    llm = get_llm()
    
    # Prepare reviews for all themes
    themes_data = {}
    for theme in top_themes:
        theme_reviews = [r for r in classified_reviews if r.get('theme') == theme]
        # Use up to 10 reviews per theme for context
        themes_data[theme] = theme_reviews[:10]
    
    # Build combined prompt for all themes
    themes_text = ""
    for theme, theme_reviews in themes_data.items():
        themes_text += f"\n## Theme: {theme}\n\n"
        themes_text += "Reviews for this theme:\n"
        for i, review in enumerate(theme_reviews, 1):
            rating = review.get('rating', 0)
            text = review.get('text', '')
            themes_text += f"Review {i} (Rating: {rating}/5): {text}\n\n"
    
    prompt = f"""You are a Product Strategist analyzing user reviews for the Groww investment app.

You need to generate actionable insights for {len(top_themes)} themes. For EACH theme, provide:

1. **Problem Statement**: Provide THREE specific bullet points that capture the major problems identified for this theme based on the reviews. Each bullet point should be a concise statement of a specific issue.

2. **Verbatim Quote**: Select ONE exact quote from the reviews for this theme (copy it word-for-word, no modifications). This quote should best represent the problem or feedback. IMPORTANT: The quote must be 100% verbatim and COMPLETE - include the entire quote, do not truncate it. Copy it exactly as written from the reviews.

3. **Action Items**: Propose TWO specific, technical action items to address the problems. These must be product-specific to Groww (e.g., "Add stop-loss UI in delivery trades tab", "Implement OTP auto-read for UPI transactions", etc.). Each action item should be a clear, actionable statement. Do not suggest generic solutions.

{themes_text}

**Output Format** (JSON only):
Return a JSON array with one object per theme, each containing:
{{
    "theme": "Theme Name",
    "problem_statements": ["Problem bullet point 1", "Problem bullet point 2", "Problem bullet point 3"],
    "verbatim_quote": "Complete exact quote from reviews (copy verbatim, do not truncate)",
    "action_items": ["Action item 1", "Action item 2"]
}}

Example format:
[
    {{
        "theme": "Theme 1",
        "problem_statements": ["Problem 1", "Problem 2", "Problem 3"],
        "verbatim_quote": "Complete user quote here without truncation...",
        "action_items": ["Action 1", "Action 2"]
    }},
    {{
        "theme": "Theme 2",
        "problem_statements": ["Problem 1", "Problem 2", "Problem 3"],
        "verbatim_quote": "Complete user quote here without truncation...",
        "action_items": ["Action 1", "Action 2"]
    }},
    {{
        "theme": "Theme 3",
        "problem_statements": ["Problem 1", "Problem 2", "Problem 3"],
        "verbatim_quote": "Complete user quote here without truncation...",
        "action_items": ["Action 1", "Action 2"]
    }}
]

Return ONLY valid JSON array, no explanations or markdown formatting.
"""
    
    try:
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        insights_list = json.loads(response_text)
        
        # Validate and verify verbatim quotes
        final_insights = []
        for insights in insights_list:
            theme = insights.get('theme', '')
            if theme not in top_themes:
                continue
            
            verbatim_quote = insights.get('verbatim_quote', '')
            theme_reviews = themes_data.get(theme, [])
            
            # Verify quote exists in reviews and use FULL quote
            if verbatim_quote:
                quote_found = False
                for review in theme_reviews:
                    review_text = review.get('text', '')
                    # Check if LLM's quote matches any part of the review
                    if verbatim_quote.lower() in review_text.lower():
                        quote_found = True
                        # Use the FULL review text as the quote (verbatim)
                        verbatim_quote = review_text  # Use complete review text
                        break
                    # Also check if review text contains the quote (reverse match)
                    elif review_text.lower() in verbatim_quote.lower():
                        quote_found = True
                        # LLM provided a longer quote, use it
                        break
                
                if not quote_found and theme_reviews:
                    # Fallback: use a full quote from reviews (don't truncate)
                    for review in theme_reviews:
                        text = review.get('text', '')
                        if len(text) > 50:
                            verbatim_quote = text  # Use full quote, don't truncate
                            break
            elif theme_reviews:
                # If no quote from LLM, use full review text
                for review in theme_reviews:
                    text = review.get('text', '')
                    if len(text) > 50:
                        verbatim_quote = text  # Use full quote
                        break
            
            # Extract problem statements (should be a list of 3)
            problem_statements = insights.get('problem_statements', [])
            if isinstance(problem_statements, str):
                # Fallback: split by newline or period if it's a string
                problem_statements = [p.strip() for p in problem_statements.replace('\n', '.').split('.') if p.strip()][:3]
            if not isinstance(problem_statements, list) or len(problem_statements) < 3:
                # Fallback: create default problem statements
                problem_statements = [
                    f'User feedback on {theme}',
                    f'Issues identified in {theme}',
                    f'Improvements needed for {theme}'
                ][:3]
            
            # Extract action items (should be a list of 2)
            action_items = insights.get('action_items', [])
            if isinstance(action_items, str):
                # Fallback: split by newline or period if it's a string
                action_items = [a.strip() for a in action_items.replace('\n', '.').split('.') if a.strip()][:2]
            if not isinstance(action_items, list) or len(action_items) < 2:
                # Fallback: create default action items
                action_items = [
                    f'Review and improve {theme} based on user feedback',
                    f'Implement fixes for {theme} issues'
                ][:2]
            
            final_insights.append({
                'theme': theme,
                'problem_statements': problem_statements[:3],  # Ensure max 3
                'verbatim_quote': verbatim_quote,
                'action_items': action_items[:2]  # Ensure max 2
            })
        
        print(f"✓ Generated insights for {len(final_insights)} themes")
        return final_insights
    
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        # Fallback: create basic insights for each theme
        insights_list = []
        for theme in top_themes:
            theme_reviews = themes_data.get(theme, [])
            full_quote = theme_reviews[0].get('text', '') if theme_reviews else ''
            insights_list.append({
                'theme': theme,
                'problem_statements': [
                    f'User feedback on {theme}',
                    f'Issues identified in {theme}',
                    f'Improvements needed for {theme}'
                ],
                'verbatim_quote': full_quote,
                'action_items': [
                    f'Review and improve {theme} based on user feedback',
                    f'Implement fixes for {theme} issues'
                ]
            })
        return insights_list
    except Exception as e:
        print(f"Error generating insights: {e}")
        # Fallback
        insights_list = []
        for theme in top_themes:
            theme_reviews = themes_data.get(theme, [])
            full_quote = theme_reviews[0].get('text', '') if theme_reviews else ''
            insights_list.append({
                'theme': theme,
                'problem_statements': [
                    f'User feedback on {theme}',
                    f'Issues identified in {theme}',
                    f'Improvements needed for {theme}'
                ],
                'verbatim_quote': full_quote,
                'action_items': [
                    f'Review and improve {theme} based on user feedback',
                    f'Implement fixes for {theme} issues'
                ]
            })
        return insights_list


def strategist_node(state: dict) -> dict:
    """
    LangGraph node function for generating strategic insights.
    
    Args:
        state: ReviewState dict with classified_reviews
    
    Returns:
        Updated state with top_themes populated
    """
    state = state.copy()
    
    try:
        classified_reviews = state.get('classified_reviews', [])
        
        if not classified_reviews:
            state['errors'] = state.get('errors', [])
            state['errors'].append("Strategist: No classified reviews to analyze")
            state['top_themes'] = []
            return state
        
        # Generate insights for top 3 themes
        top_themes = generate_top_themes_insights(classified_reviews, top_n=3)
        
        state['top_themes'] = top_themes
        state['errors'] = state.get('errors', [])
        
    except Exception as e:
        error_msg = f"Strategist error: {str(e)}"
        state['errors'] = state.get('errors', [])
        state['errors'].append(error_msg)
        state['top_themes'] = []
    
    return state

