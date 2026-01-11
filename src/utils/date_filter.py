from datetime import datetime
from typing import List, Dict
from src.config.settings import settings


def parse_review_date(date_str: str) -> datetime:
    """
    Parse review date from Play Store format to datetime.
    Handles various date formats that Play Store might use.
    """
    # Common Play Store date formats:
    # "30 October 2025", "Oct 30, 2025", "30/10/2025", etc.
    
    # Try different parsing strategies
    date_formats = [
        "%d %B %Y",      # "30 October 2025"
        "%B %d, %Y",     # "October 30, 2025"
        "%d %b %Y",      # "30 Oct 2025"
        "%b %d, %Y",     # "Oct 30, 2025"
        "%d/%m/%Y",      # "30/10/2025"
        "%m/%d/%Y",      # "10/30/2025"
        "%Y-%m-%d",      # "2025-10-30"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # If all parsing fails, raise an error
    raise ValueError(f"Unable to parse date: {date_str}")


def filter_reviews_by_date(reviews: List[Dict], cutoff_date: datetime = None) -> List[Dict]:
    """
    Filter reviews to only include those posted within the last 60 days.
    
    Args:
        reviews: List of review dicts with 'date' key (string format)
        cutoff_date: Date to filter from (defaults to settings.CUTOFF_DATE)
    
    Returns:
        Filtered list of reviews
    """
    if cutoff_date is None:
        cutoff_date = settings.CUTOFF_DATE
    
    filtered_reviews = []
    
    for review in reviews:
        try:
            review_date = parse_review_date(review.get("date", ""))
            # Include reviews on or after the cutoff date
            if review_date >= cutoff_date:
                filtered_reviews.append(review)
        except (ValueError, KeyError) as e:
            # Skip reviews with invalid dates, but log the error
            continue
    
    return filtered_reviews

