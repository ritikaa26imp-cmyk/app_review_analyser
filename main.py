#!/usr/bin/env python3
"""
Main orchestrator for the Groww Weekly Pulse Multi-Agent System
Executes the complete pipeline: Extract → Classify → Strategist → Editor → Email
"""

import sys
import json
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph.graph import create_workflow
from src.utils.email_sender import send_weekly_pulse_email
from src.config.settings import settings


def main():
    """
    Main entry point for the Weekly Pulse pipeline.
    """
    print("=" * 70)
    print("Groww Weekly Pulse - Multi-Agent System")
    print("=" * 70)
    print(f"\nExecution Date: {settings.CURRENT_DATE.strftime('%Y-%m-%d')}")
    print(f"Cutoff Date: {settings.CUTOFF_DATE.strftime('%Y-%m-%d')} (Last {settings.CUTOFF_DAYS} days)")
    print(f"Target URL: {settings.GROWW_PLAY_STORE_URL}")
    print("\n" + "-" * 70)
    print("Starting Pipeline Execution...")
    print("-" * 70 + "\n")
    
    try:
        # Create workflow
        print("Initializing LangGraph workflow...")
        workflow = create_workflow()
        print("✓ Workflow initialized\n")
        
        # Initialize state
        initial_state = {
            'raw_reviews': [],
            'classified_reviews': [],
            'top_themes': [],
            'final_report': '',
            'errors': []
        }
        
        # Execute workflow
        print("=" * 70)
        print("Executing Workflow")
        print("=" * 70)
        print("\nAgent 1: Extractor - Extracting reviews from Play Store...")
        print("Agent 2: Classifier - Classifying reviews into themes...")
        print("Agent 3: Strategist - Identifying top themes and generating insights...")
        print("Agent 4: Editor - Formatting final report...\n")
        
        # Invoke workflow
        final_state = workflow.invoke(initial_state)
        
        print("\n" + "=" * 70)
        print("Pipeline Execution Complete")
        print("=" * 70)
        
        # Check for errors
        errors = final_state.get('errors', [])
        if errors:
            print(f"\n⚠ Warnings/Errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
        
        # Display results
        raw_reviews_count = len(final_state.get('raw_reviews', []))
        classified_reviews_count = len(final_state.get('classified_reviews', []))
        top_themes_count = len(final_state.get('top_themes', []))
        final_report = final_state.get('final_report', '')
        
        print(f"\nResults Summary:")
        print(f"  - Raw reviews extracted: {raw_reviews_count}")
        print(f"  - Reviews classified: {classified_reviews_count}")
        print(f"  - Top themes identified: {top_themes_count}")
        print(f"  - Final report generated: {'Yes' if final_report else 'No'}")
        
        if final_report:
            from src.agents.editor import count_words
            word_count = count_words(final_report)
            print(f"  - Report word count: {word_count} / {settings.MAX_REPORT_WORDS}")
            
            print("\n" + "-" * 70)
            print("Final Report Preview")
            print("-" * 70)
            print(final_report[:500] + "..." if len(final_report) > 500 else final_report)
            print()
            
            # Save report to file
            report_file = 'weekly_pulse_report.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(final_report)
            print(f"✓ Report saved to: {report_file}")
            
            # Send email
            print("\n" + "-" * 70)
            print("Sending Email")
            print("-" * 70)
            
            if settings.GMAIL_APP_PASSWORD:
                try:
                    email_sent = send_weekly_pulse_email(final_report)
                    if email_sent:
                        print(f"\n✓ Email sent successfully to {settings.RECIPIENT_EMAIL}")
                    else:
                        print(f"\n✗ Failed to send email. Check error messages above.")
                except Exception as e:
                    print(f"\n✗ Error sending email: {e}")
            else:
                print("\n⚠ GMAIL_APP_PASSWORD not configured in .env")
                print("  Email sending skipped. To enable email, add GMAIL_APP_PASSWORD to .env")
        
        else:
            print("\n⚠ No final report generated. Check errors above.")
        
        print("\n" + "=" * 70)
        print("Execution Complete")
        print("=" * 70)
        
        # Exit with appropriate code
        if errors:
            sys.exit(1)  # Exit with error code if there are errors
        else:
            sys.exit(0)  # Success
    
    except KeyboardInterrupt:
        print("\n\n⚠ Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

