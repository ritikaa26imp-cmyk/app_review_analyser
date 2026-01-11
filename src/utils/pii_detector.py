import re
from typing import List, Tuple


def detect_names(text: str) -> List[str]:
    """
    Detect potential names in text.
    Looks for patterns like:
    - "by [Name]" or "By [Name]"
    - Names after common prefixes
    - Capitalized words that might be names
    """
    names = []
    
    # Pattern 1: "by [Name]" or "By [Name]" followed by capitalized words
    by_pattern = r'\b[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    matches = re.findall(by_pattern, text)
    names.extend(matches)
    
    # Pattern 2: Common name patterns (capitalized words, 1-3 words)
    # This is a simple heuristic - might need refinement
    name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)'
    # Extract names that appear to be full names (2 capitalized words)
    potential_names = re.findall(name_pattern, text)
    # Filter out common false positives
    false_positives = {'Play Store', 'Google Play', 'Groww', 'App Store', 
                      'Customer Support', 'User Review', 'Review Text'}
    names.extend([n for n in potential_names if n not in false_positives and n not in names])
    
    return names


def detect_emails(text: str) -> List[str]:
    """
    Detect email addresses in text.
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails


def detect_user_ids(text: str) -> List[str]:
    """
    Detect user IDs or usernames (alphanumeric strings that might be IDs).
    This is a conservative pattern to avoid false positives.
    """
    # Pattern for user IDs: alphanumeric strings of 8+ characters
    # that aren't URLs or email parts
    user_id_pattern = r'\b(?<!@)(?<!http://)(?<!https://)[A-Za-z0-9]{8,}\b'
    matches = re.findall(user_id_pattern, text)
    
    # Filter out common false positives
    false_positives = {'play.google', 'groww.com', 'https://'}
    filtered = [m for m in matches if not any(fp in m.lower() for fp in false_positives)]
    
    return filtered


def anonymize_pii(text: str) -> str:
    """
    Anonymize PII in text by replacing names with [User].
    
    Args:
        text: Input text containing potential PII
    
    Returns:
        Text with PII anonymized (names replaced with [User])
    """
    anonymized_text = text
    
    # Detect and replace names
    names = detect_names(text)
    for name in names:
        # Replace the full name with [User]
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(name) + r'\b'
        anonymized_text = re.sub(pattern, '[User]', anonymized_text, flags=re.IGNORECASE)
    
    # Detect and replace emails (replace with [email])
    emails = detect_emails(text)
    for email in emails:
        anonymized_text = anonymized_text.replace(email, '[email]')
    
    # Note: User IDs are less commonly in review text, so we'll be conservative
    # and not replace them unless they're clearly problematic
    
    return anonymized_text


def anonymize_review_dict(review: dict) -> dict:
    """
    Anonymize PII in a review dictionary.
    
    Args:
        review: Review dict with keys like 'text', 'rating', 'date'
    
    Returns:
        Review dict with anonymized text
    """
    anonymized_review = review.copy()
    
    if 'text' in anonymized_review:
        anonymized_review['text'] = anonymize_pii(anonymized_review['text'])
    
    # Also check other fields that might contain PII
    for key in ['quote', 'verbatim_quote', 'problem_statement']:
        if key in anonymized_review:
            anonymized_review[key] = anonymize_pii(anonymized_review[key])
    
    return anonymized_review

