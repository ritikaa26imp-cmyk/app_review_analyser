# Groww Weekly Pulse Multi-Agent System

An automated pipeline that extracts, categorizes, and analyzes user feedback from the Groww Google Play Store page using a 4-agent LangGraph system with Groq LLM integration.

## 🎯 Overview

This system automates the process of gathering user feedback from Google Play Store reviews, categorizing them into themes, identifying top problems, and generating actionable insights - all delivered via email in a formatted weekly report.

## 🏗️ Architecture

The system uses a **4-agent sequential pipeline** orchestrated by LangGraph:

```
Extractor → Classifier → Strategist → Editor → Email
```

### Agents

1. **Agent 1: Extractor (The Gatekeeper)**
   - Navigates to Groww Play Store page
   - Extracts reviews from the last 60 days
   - Filters and structures review data

2. **Agent 2: Classifier (The Organizer)**
   - Classifies reviews into 5 themes using Groq LLM
   - Themes: Onboarding & Verification, Customer Support, Trading Experience, Statements & Reports, Overall Usability

3. **Agent 3: Strategist (The Analyst)**
   - Identifies top 3 themes by volume/severity
   - Generates problem statements, verbatim quotes, and action items

4. **Agent 4: Editor (Compliance & Delivery)**
   - Anonymizes PII (names, emails)
   - Formats final report (≤250 words)
   - Ensures verbatim quotes are complete

## 📋 Prerequisites

- Python 3.9+
- Playwright browsers installed
- Groq API key(s) - [Get from Groq Console](https://console.groq.com/keys)
- Gmail app password (for email sending)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd groww-product-reviewer-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install
```

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Email Settings
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=recipient@example.com

# Groq API Keys
GROQ_API_KEY_CLASSIFIER=your_groq_api_key_here
GROQ_API_KEY_STRATEGIST=your_groq_api_key_here
GROQ_API_KEY_FALLBACK=your_groq_api_key_here
```

### 4. Set Up Gmail App Password

1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Enable IMAP: Gmail Settings → Forwarding and POP/IMAP → Enable IMAP
4. Add the app password to `.env` file

### 5. Run the Pipeline

```bash
python3 main.py
```

The system will:
1. Extract reviews from Play Store
2. Classify them into themes
3. Generate insights for top themes
4. Format and send the report via email

## 📁 Project Structure

```
groww-product-reviewer-agent/
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── src/
    ├── agents/
    │   ├── extractor.py         # Agent 1: Play Store extraction
    │   ├── classifier.py         # Agent 2: Review classification
    │   ├── strategist.py         # Agent 3: Insight generation
    │   └── editor.py             # Agent 4: Report formatting
    ├── graph/
    │   ├── state.py              # LangGraph state schema
    │   └── graph.py              # LangGraph workflow definition
    ├── config/
    │   ├── settings.py           # Configuration management
    │   └── classification_examples.py  # Theme examples
    └── utils/
        ├── email_sender.py       # Gmail SMTP email sending
        ├── pii_detector.py       # PII anonymization
        └── date_filter.py        # Date filtering utilities
```

## 🔐 Security

**Important:** API keys and passwords are never hardcoded in the source code. They must be configured in the `.env` file:

- ✅ `.env` file is gitignored (never committed)
- ✅ All sensitive data loaded from environment variables
- ✅ No API keys in source code

**Never commit your `.env` file to version control!**

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GMAIL_USER` | Gmail address for sending emails | Yes |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password | Yes |
| `RECIPIENT_EMAIL` | Email address to receive reports | Yes |
| `GROQ_API_KEY_CLASSIFIER` | Groq API key for Classifier agent | Yes |
| `GROQ_API_KEY_STRATEGIST` | Groq API key for Strategist agent | Yes |
| `GROQ_API_KEY_FALLBACK` | Fallback Groq API key | No |
| `GROWW_PLAY_STORE_URL` | Play Store URL (default provided) | No |
| `CUTOFF_DAYS` | Days to look back for reviews (default: 60) | No |

### API Keys Setup

**Groq API Keys:**
1. Sign up at [Groq Console](https://console.groq.com/)
2. Navigate to API Keys section
3. Create API keys for each agent (or use one for all)
4. Add keys to `.env` file

**Different API Keys Per Agent:**
- Recommended for better rate limit management
- Each agent can use its own Groq API key
- Fallback key used if primary keys fail

## 📊 Output Format

The system generates a formatted weekly report with:

```
Groww Weekly Pulse - [Date]

Main Problems identified:

**Problem Theme 1: [Theme Name]**

Major problem identified:
• Problem statement 1
• Problem statement 2
• Problem statement 3

**User Quote**
[Complete verbatim user quote - never truncated]

Action items:
• Action item 1
• Action item 2
```

The report is:
- Saved to `weekly_pulse_report.txt`
- Sent via email to the configured recipient
- Limited to ~250 words (quotes are always complete)

## 🔧 Technical Details

### Technology Stack

- **LangGraph**: Multi-agent orchestration
- **Groq (Llama 3.1 8B Instant)**: Fast LLM inference
- **Playwright**: Headless browser automation
- **Python-dotenv**: Environment variable management
- **smtplib**: Email sending via Gmail SMTP

### Classification Themes

1. **Onboarding and Verification**: Account setup, KYC, activation issues
2. **Customer Support**: Response times, feedback handling
3. **Trading Experience**: Order execution, slippage, trading features
4. **Statements & Reports**: P&L reports, data accuracy, technical glitches
5. **Overall Usability**: UI/UX, navigation, general app experience

```

For issues or questions, please contact the project maintainer @ritikaa26.imp@gmail.com

---
