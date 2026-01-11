import json
from typing import List, Dict
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
from src.config.settings import settings
from src.utils.date_filter import filter_reviews_by_date, parse_review_date


def extract_play_store_reviews(store_url: str, max_retries: int = 3) -> List[Dict]:
    """
    Extract reviews from Google Play Store.
    
    Args:
        store_url: URL of the Play Store app page
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of review dicts: [{rating, date, text}, ...]
    """
    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Navigate to Play Store page
                print(f"Navigating to {store_url}...")
                page.goto(store_url, wait_until='networkidle', timeout=30000)
                
                # Click "See all reviews" button
                # The button text might vary, try multiple selectors
                print("Looking for 'See all reviews' button...")
                try:
                    # Try finding button by text (various possible texts)
                    review_button = page.locator('text=/See.*review/i').first
                    if not review_button.is_visible(timeout=5000):
                        # Try alternative selector
                        review_button = page.locator('button:has-text("reviews")').first
                    review_button.click(timeout=10000)
                except Exception as e:
                    print(f"Could not find review button, trying alternative: {e}")
                    # Alternative: look for link with review count
                    review_link = page.locator('a[href*="review"]').first
                    review_link.click(timeout=10000)
                
                # Wait for modal dialog to appear
                print("Waiting for review modal...")
                page.wait_for_timeout(3000)  # Wait for modal to load
                
                # Try to find modal/dialog - Play Store uses div[role="dialog"]
                try:
                    modal = page.locator('div[role="dialog"]').first
                    modal.wait_for(state='visible', timeout=10000)
                except PlaywrightTimeoutError:
                    # If modal doesn't appear, reviews might be on the page itself
                    print("Modal not found, checking if reviews are on the page...")
                    modal = page  # Use page as fallback
                    return []
                
                # Ensure "Most relevant" is selected (it's usually default, but verify)
                print("Ensuring 'Most relevant' filter is selected...")
                try:
                    # Try to find and click "Most relevant" if not already selected
                    # The dropdown shows "Most relevant" when it's the active sort
                    most_relevant = modal.locator('text=/Most relevant/i').first
                    if most_relevant.is_visible(timeout=2000):
                        # If visible, it's likely already selected, but verify it's clickable/active
                        pass  # "Most relevant" is typically the default
                except:
                    pass  # If not found, assume it's the default
                
                # Scroll to load reviews (infinite scroll)
                print("Scrolling to load reviews...")
                reviews_data = []
                last_review_count = 0
                scroll_attempts = 0
                max_scroll_attempts = 50  # Increased limit to get more reviews
                no_change_count = 0  # Track consecutive scrolls with no new reviews
                
                while scroll_attempts < max_scroll_attempts:
                    # Extract reviews from current view - Play Store uses header.c1bOId for review headers
                    review_headers = modal.locator('header.c1bOId').all()
                    current_count = len(review_headers)
                    
                    if current_count == last_review_count:
                        no_change_count += 1
                        # If no new reviews after 3 consecutive scrolls, we've likely reached the end
                        if no_change_count >= 3 and current_count > 0:
                            break
                    else:
                        no_change_count = 0  # Reset counter when new reviews are found
                    
                    last_review_count = current_count
                    
                    # Scroll down within the modal - scroll to bottom for better lazy loading
                    modal.evaluate('element => { element.scrollTop = element.scrollHeight - 100; }')
                    page.wait_for_timeout(3000)  # Increased wait time for lazy loading
                    
                    scroll_attempts += 1
                
                print(f"Found {last_review_count} review elements, extracting data...")
                
                # Get all review headers and texts - Play Store structure
                review_headers = modal.locator('header.c1bOId').all()
                review_texts = modal.locator('div.h3YV2d').all()
                
                # Match headers with texts (they should be in the same order)
                for i, header in enumerate(review_headers):
                    try:
                        # Extract rating from aria-label (e.g., "Rated 5 stars out of five stars")
                        rating_elem = header.locator('div.iXRFPc').first
                        rating_text = rating_elem.get_attribute('aria-label') or ""
                        rating = _parse_rating(rating_text)
                        
                        # Extract date - Play Store uses .bp9Aid class inside header
                        date_elem = header.locator('span.bp9Aid').first
                        date_text = date_elem.text_content() or ""
                        date_str = _normalize_date(date_text)
                        
                        # Get corresponding review text (should be at same index)
                        if i < len(review_texts):
                            review_text = review_texts[i].text_content() or ""
                        else:
                            review_text = ""
                        
                        if review_text.strip() and rating > 0:  # Only add valid reviews
                            reviews_data.append({
                                'rating': rating,
                                'date': date_str,
                                'text': review_text.strip()
                            })
                    except Exception as e:
                        # Skip reviews that fail to parse
                        continue
                
                browser.close()
                
                # Filter reviews by date (last 60 days)
                print(f"Filtering {len(reviews_data)} reviews by date...")
                filtered_reviews = filter_reviews_by_date(reviews_data)
                print(f"Found {len(filtered_reviews)} reviews within last 60 days")
                
                return filtered_reviews
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print("All retry attempts exhausted")
                return []
            continue
    
    return []


def _parse_rating(rating_text: str) -> int:
    """
    Parse rating from text (e.g., "4 stars" -> 4)
    """
    if not rating_text:
        return 0
    
    # Extract number from rating text
    import re
    match = re.search(r'(\d+)', rating_text)
    if match:
        rating = int(match.group(1))
        return min(max(rating, 1), 5)  # Clamp between 1 and 5
    return 0


def _normalize_date(date_text: str) -> str:
    """
    Normalize date text to YYYY-MM-DD format.
    This is a helper - actual parsing is done in date_filter.py
    """
    # Return as-is, let date_filter.py handle parsing
    # But try to clean up common formats
    date_text = date_text.strip()
    
    # Common Play Store formats: "30 October 2025", "Oct 30, 2025", etc.
    return date_text


def extract_node(state: dict) -> dict:
    """
    LangGraph node function for extracting reviews.
    
    Args:
        state: ReviewState dict
    
    Returns:
        Updated state with raw_reviews populated
    """
    state = state.copy()
    
    try:
        reviews = extract_play_store_reviews(settings.GROWW_PLAY_STORE_URL)
        state['raw_reviews'] = reviews
        state['errors'] = state.get('errors', [])
        
        if not reviews:
            state['errors'].append("Extractor: No reviews found or extraction failed")
    except Exception as e:
        error_msg = f"Extractor error: {str(e)}"
        state['errors'] = state.get('errors', [])
        state['errors'].append(error_msg)
        state['raw_reviews'] = []
    
    return state

