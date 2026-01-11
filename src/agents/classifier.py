import json
from typing import List, Dict
from langchain_groq import ChatGroq
from src.config.settings import settings
from src.config.classification_examples import get_classification_examples


# Initialize Groq LLM
def get_llm():
    """Initialize and return Groq LLM client for Classifier Agent"""
    return ChatGroq(
        model="llama-3.1-8b-instant",  # Fast and efficient model
        groq_api_key=settings.GROQ_API_KEY_CLASSIFIER,
        temperature=0.1  # Low temperature for consistent classification
    )


def create_classification_prompt(reviews: List[Dict], examples: Dict) -> str:
    """
    Create the classification prompt with system instructions and examples.
    
    Args:
        reviews: List of review dicts to classify
        examples: Classification examples dict
    
    Returns:
        Formatted prompt string
    """
    # Build examples section
    examples_text = "\n## Classification Examples:\n\n"
    
    for theme, theme_examples in examples.items():
        examples_text += f"### {theme}:\n"
        if theme_examples.get("positive"):
            examples_text += f"Positive: {theme_examples['positive'][0]}\n"
        if theme_examples.get("negative"):
            examples_text += f"Negative: {theme_examples['negative'][0]}\n"
        examples_text += "\n"
    
    # Build reviews JSON for classification
    reviews_json = json.dumps(reviews, indent=2, ensure_ascii=False)
    
    prompt = f"""You are a high-fidelity Semantic Categorization Agent. Your purpose is to process structured user reviews and accurately assign each one to a specific product theme based on its primary content.

## Categorization Themes & Definitions

You must map every review to exactly one of the following five themes:

**Onboarding and Verification:**
Definition: Relates to account setup, KYC documentation, e-sign, and account activation (e.g., NSE/BSE activation).
Positive Signifiers: "simple setup," "easy to start," "fantastic interface for new users."
Negative Signifiers: "16+ days for verification," "account not activated," "unable to buy/sell after signup."

**Customer Support:**
Definition: Evaluates the responsiveness, empathy, and resolution speed of the help desk and feedback channels.
Positive Signifiers: "resolved quickly," "reliable service," "clear communication."
Negative Signifiers: "delayed response," "not interested in feedback," "team not responding on charts."

**Trading Experience:**
Definition: Focuses on the core utility of buying/selling stocks/F&O, order execution speed, GTT orders, and slippage.
Positive Signifiers: "smoothest app for trading," "GTT orders are beginner-friendly," "clean buy/sell logic."
Negative Signifiers: "high slippage during exit," "executed amount different from booked profit," "fraud app due to losses."

**Statements & Reports:**
Definition: Pertains to the accuracy of P&L reports, data filters, and technical glitches in input fields (like the 0.02 freeze).
Positive Signifiers: "organized investments," "clear charts," "well-organized SIPs."
Negative Signifiers: "duplicate stocks in P&L," "malformed data filters," "amount freezes at 0.02 during share purchase."

**Overall Usability:**
Definition: General app navigation, UI design logic, and friction introduced by recent layout updates.
Positive Signifiers: "clean interface," "user-friendly for beginners," "everything well organized."
Negative Signifiers: "recent update not good," "too many clicks to open stock details," "confusing chart placement."

{examples_text}

## Core Classification Logic

- **Dominant Theme Rule**: If a review mentions multiple themes, assign it to the theme representing the most severe pain point or the primary focus of the praise.
- **Neutral Category**: If a review is too vague (e.g., "Good app"), default to "Overall Usability".
- **Consistency**: Use the provided positive/negative training examples to resolve edge cases; ensure 99% accuracy by strictly adhering to the definitions above.

## Key Constraints

- **No Data Alteration**: Do not modify the rating, date, or text fields.
- **PII Sensitivity**: Do not add or generate any new user identifiers.
- **Output Format**: Return the original JSON objects with a new key-value pair: "theme": "Theme Name".

## Reviews to Classify:

{reviews_json}

## Instructions:

For each review in the JSON array above, classify it into exactly ONE of the five themes:
- "Onboarding and Verification"
- "Customer Support"
- "Trading Experience"
- "Statements & Reports"
- "Overall Usability"

Return ONLY a valid JSON array with the same structure, but with a "theme" field added to each review object. Do not include any explanations or markdown formatting, only the JSON array.
"""
    
    return prompt


def classify_reviews_batch(reviews: List[Dict], llm, examples: Dict) -> List[Dict]:
    """
    Classify a batch of reviews using Gemini LLM.
    
    Args:
        reviews: List of review dicts to classify
        llm: Gemini LLM instance
        examples: Classification examples dict
    
    Returns:
        List of classified reviews with theme field added
    """
    if not reviews:
        return []
    
    prompt = create_classification_prompt(reviews, examples)
    
    try:
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Extract JSON from response (handle markdown code blocks if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        classified_reviews = json.loads(response_text)
        
        # Validate that all reviews have theme field
        for review in classified_reviews:
            if "theme" not in review:
                review["theme"] = "Overall Usability"  # Default fallback
        
        return classified_reviews
    
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        print(f"Response was: {response_text[:500]}")
        # Fallback: assign default theme
        for review in reviews:
            review["theme"] = "Overall Usability"
        return reviews
    except Exception as e:
        print(f"Error during classification: {e}")
        # Fallback: assign default theme
        for review in reviews:
            review["theme"] = "Overall Usability"
        return reviews


def classify_reviews(reviews: List[Dict], batch_size: int = 10) -> List[Dict]:
    """
    Classify reviews into themes using Gemini LLM.
    Processes reviews in batches for efficiency.
    
    Args:
        reviews: List of review dicts with {rating, date, text}
        batch_size: Number of reviews to process per LLM call
    
    Returns:
        List of classified reviews with {rating, date, text, theme}
    """
    if not reviews:
        return []
    
    # Load classification examples
    examples = get_classification_examples()
    
    # Initialize LLM
    llm = get_llm()
    
    # Process reviews in batches
    classified_reviews = []
    total_batches = (len(reviews) + batch_size - 1) // batch_size
    
    print(f"Classifying {len(reviews)} reviews in {total_batches} batch(es)...")
    
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} reviews)...")
        
        batch_classified = classify_reviews_batch(batch, llm, examples)
        classified_reviews.extend(batch_classified)
    
    print(f"✓ Classified {len(classified_reviews)} reviews")
    
    return classified_reviews


def classify_node(state: dict) -> dict:
    """
    LangGraph node function for classifying reviews.
    
    Args:
        state: ReviewState dict with raw_reviews
    
    Returns:
        Updated state with classified_reviews populated
    """
    state = state.copy()
    
    try:
        raw_reviews = state.get('raw_reviews', [])
        
        if not raw_reviews:
            state['errors'] = state.get('errors', [])
            state['errors'].append("Classifier: No raw reviews to classify")
            state['classified_reviews'] = []
            return state
        
        # Classify reviews (process all reviews in one API call)
        classified_reviews = classify_reviews(raw_reviews, batch_size=100)
        
        state['classified_reviews'] = classified_reviews
        state['errors'] = state.get('errors', [])
        
    except Exception as e:
        error_msg = f"Classifier error: {str(e)}"
        state['errors'] = state.get('errors', [])
        state['errors'].append(error_msg)
        state['classified_reviews'] = []
    
    return state

