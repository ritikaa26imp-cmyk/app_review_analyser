"""
Classification examples for the 5 review themes.
Used as few-shot examples for the Classifier Agent.
"""

THEME_EXAMPLES = {
    "Onboarding and Verification": {
        "positive": [
            "Easy to use for beginners in the stock market. Groww has made investing incredibly simple and stress-free. The user interface is fantastic and I had no issues setting up my account. Highly recommended for anyone new to investing!"
        ],
        "negative": [
            "the worst app for trading taking almost 16+ days for verification of your account you will be unable to buy or sell stocks if your NSE account is not activated and if you ask them for help they just say tomorrow it will be activated there tomorrow never comes.. I called multiple times but no solution for the problem"
        ]
    },
    "Customer Support": {
        "positive": [
            "What I appreciate most is their customer support. Whenever I had an issue or a query, it was resolved quickly and clearly. Overall, their service feels reliable and user friendly, and it makes investing much easier."
        ],
        "negative": [
            "the customer support is very delayed and no one is interested in taking the feedback as well. no updates to groww charts from 3.5 months, groww team is not responding on this at all. Your what's new section writings contain more creativity than your platforms."
        ]
    },
    "Trading Experience": {
        "positive": [
            "Groww is one of the smoothest and easiest apps for beginners in trading and investing. The interface is clean, buying and selling stocks is simple, and GTT orders make it beginner-friendly. However, the app still needs a few advanced features like stop-loss / take-profit for delivery trades and trailing stop-loss options for swing traders. Adding those would make Groww perfect for both new and active users. Overall, it's great for starting out, learning, and building a long-term portfolio"
        ],
        "negative": [
            "I have been using this app for some time now. But when I started intraday trading, i encountered its high slippage. For example, I book a trade at a profit of around 12000 using their exit button, the executed amount would be 10000. There have been times when booked a profit of more than 2000 still the executed profit was not only less but in loss -749. This is higly disappointing. Now I'm looking for a new broker app. Too much Fraud app. I have lost 20000 rupees on this app. Hence",
            "Under reports and Statement section when we view our Stocks P&L the stock are being shown multiple times like duplicates. When we apply filter, still it's malformed data not exactly filtered in a sequence like how to low or low to high. While buying shares when we try to enter amount most of the time it's freezez at 0.02 with red marks by default and I manually have to back press and clear all amount and then enter the correct amount instead it should allow to enter the amount we want not 0.02"
        ]
    },
    "Statements & Reports": {
        "positive": [
            # Note: User didn't provide positive examples for this theme
            # Will use general positive statements about reports
        ],
        "negative": [
            "Under reports and Statement section when we view our Stocks P&L the stock are being shown multiple times like duplicates. When we apply filter, still it's malformed data not exactly filtered in a sequence like how to low or low to high. While buying shares when we try to enter amount most of the time it's freezez at 0.02 with red marks by default and I manually have to back press and clear all amount and then enter the correct amount instead it should allow to enter the amount we want not 0.02"
        ]
    },
    "Overall Usability": {
        "positive": [
            "Groww is one of the best and most user-friendly investment apps. The interface is very clean and easy to understand, even for beginners. Mutual funds, stocks, SIPs, and other investments are well organized, and transactions are smooth and fast. The app provides clear information, charts, and updates which help in making better decisions. Customer support is also responsive. Overall, Groww makes investing simple and stress-free. but i want Dragging SL(stop loss) or TP(target point ) option."
        ],
        "negative": [
            "recent update is not good. on click of any stock it will ask for view chart set alert or need to open stock details. I am clicking on stock name to see the details right it's obvious. This is not user friendly. Instead changes can be made like on click of stock name you can make the stock details to open and on click of chart place you can make chart to open. similar to on click of market price how it will change to to 52w high low"
        ]
    }
}


def get_classification_examples() -> dict:
    """Returns the classification examples dictionary"""
    return THEME_EXAMPLES

