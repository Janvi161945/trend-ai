#!/usr/bin/env python3
"""
Demo script to showcase the new trend analysis capabilities.

This script demonstrates:
1. Topic extraction with confidence scoring
2. Reel idea generation
3. Multi-signal trend detection
"""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractors.topic_extractor_json import extract_topic_with_confidence, batch_extract_topics
from src.generators.reel_idea_generator import generate_reel_ideas, format_reel_idea_output
from src.scoring.multi_signal_trend_detector import (
    detect_trending_topics,
    hybrid_trend_detection,
    format_trending_output
)


def demo_topic_extraction():
    """Demo 1: Extract topics with confidence scores"""
    print("=" * 60)
    print("DEMO 1: Topic Extraction with Confidence")
    print("=" * 60)

    sample_captions = [
        "3 tax saving tips for salaried employees before March deadline",
        "SIP vs FD which is better for beginners in 2024",
        "How I built emergency fund in 6 months step by step",
        "Credit card mistakes that are costing you money every month",
        "Budget 2024 tax changes explained in simple Hindi"
    ]

    print("\nExtracting topics from sample captions...\n")

    results = batch_extract_topics(sample_captions)

    for i, result in enumerate(results, 1):
        print(f"{i}. Caption: {result['caption'][:60]}...")
        print(f"   Topic: {result['topic']}")
        print(f"   Confidence: {result['confidence']}%")
        print()


def demo_reel_idea_generation():
    """Demo 2: Generate reel ideas from captions"""
    print("\n" + "=" * 60)
    print("DEMO 2: Reel Idea Generation")
    print("=" * 60)

    sample_captions = [
        "Tax saving tips before March 31st deadline",
        "SIP vs FD comparison for beginners",
        "How to build emergency fund",
        "Credit card mistakes to avoid",
        "Budget 2024 highlights for salaried",
        "Best investment options for 2024",
        "How to save money on taxes",
        "Mutual fund SIP returns explained",
        "Stock market crash explained",
        "Personal finance tips for beginners"
    ]

    print("\nGenerating content ideas from trending captions...\n")

    ideas = generate_reel_ideas(sample_captions)

    print(format_reel_idea_output(ideas))


def demo_trend_detection():
    """Demo 3: Detect trending topics from reel data"""
    print("\n" + "=" * 60)
    print("DEMO 3: Multi-Signal Trend Detection")
    print("=" * 60)

    # Sample reel data with engagement metrics
    sample_reels = [
        {
            "caption": "Tax saving tips before March 31st deadline - save lakhs!",
            "likes": 12000,
            "comments": 340,
            "creator_name": "financeguru",
            "timestamp": "2024-03-10T10:00:00"
        },
        {
            "caption": "Last minute tax saving hacks for salaried employees",
            "likes": 8500,
            "comments": 210,
            "creator_name": "moneywizard",
            "timestamp": "2024-03-10T14:00:00"
        },
        {
            "caption": "SIP vs FD - which is better for you in 2024?",
            "likes": 15000,
            "comments": 420,
            "creator_name": "investpro",
            "timestamp": "2024-03-09T12:00:00"
        },
        {
            "caption": "Fixed Deposit vs SIP comparison for beginners",
            "likes": 9200,
            "comments": 180,
            "creator_name": "financeguru",
            "timestamp": "2024-03-09T16:00:00"
        },
        {
            "caption": "How I built Rs 5 lakh emergency fund in 1 year",
            "likes": 11000,
            "comments": 280,
            "creator_name": "savingsmom",
            "timestamp": "2024-03-08T11:00:00"
        },
        {
            "caption": "Emergency fund mistakes to avoid - lost 2 lakhs!",
            "likes": 7800,
            "comments": 150,
            "creator_name": "moneywizard",
            "timestamp": "2024-03-08T15:00:00"
        },
        {
            "caption": "5 credit card mistakes that cost me money every month",
            "likes": 13500,
            "comments": 390,
            "creator_name": "creditcardpro",
            "timestamp": "2024-03-10T09:00:00"
        },
        {
            "caption": "Budget 2024 tax changes explained in 60 seconds",
            "likes": 18000,
            "comments": 520,
            "creator_name": "taxexpert",
            "timestamp": "2024-03-07T10:00:00"
        },
        {
            "caption": "New tax regime vs old regime - which one to choose?",
            "likes": 10500,
            "comments": 310,
            "creator_name": "financeguru",
            "timestamp": "2024-03-07T14:00:00"
        },
        {
            "caption": "Mutual fund SIP returns after 10 years - shocking truth!",
            "likes": 14200,
            "comments": 380,
            "creator_name": "investpro",
            "timestamp": "2024-03-06T11:00:00"
        }
    ]

    print("\nDetecting trending topics from sample reel data...\n")

    trends = detect_trending_topics(sample_reels)

    print(format_trending_output(trends))


def demo_hybrid_approach():
    """Demo 4: Hybrid trend detection (local scoring)"""
    print("\n" + "=" * 60)
    print("DEMO 4: Hybrid Trend Detection (Local Scoring)")
    print("=" * 60)

    sample_reels = [
        {
            "caption": "Tax saving tips before March 31st",
            "likes": 12000,
            "comments": 340,
            "creator_name": "financeguru",
            "timestamp": "2024-03-10T10:00:00"
        },
        {
            "caption": "Last minute tax saving hacks",
            "likes": 8500,
            "comments": 210,
            "creator_name": "moneywizard",
            "timestamp": "2024-03-10T14:00:00"
        },
        {
            "caption": "SIP vs FD comparison",
            "likes": 15000,
            "comments": 420,
            "creator_name": "investpro",
            "timestamp": "2024-03-09T12:00:00"
        }
    ]

    print("\nUsing local scoring (faster, no API calls)...\n")

    trends = hybrid_trend_detection(sample_reels, use_llm=False)

    print(format_trending_output(trends))


def main():
    """Run all demos"""
    print("\n🎬 FINANCE REEL TREND ANALYSIS DEMO")
    print("=" * 60)
    print("\nThis demo showcases three AI-powered analysis tools:")
    print("1. Topic Extraction with Confidence")
    print("2. Reel Idea Generation")
    print("3. Multi-Signal Trend Detection")
    print("\nNote: Demos 2-4 require GROQ_API_KEY to be set.\n")

    try:
        # Demo 1: Topic Extraction
        demo_topic_extraction()

        # Demo 2: Reel Idea Generation
        demo_reel_idea_generation()

        # Demo 3: Trend Detection (LLM)
        demo_trend_detection()

        # Demo 4: Hybrid Approach (Local)
        demo_hybrid_approach()

        print("\n" + "=" * 60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Check docs/trend_analysis_guide.md for detailed documentation")
        print("2. Integrate these tools into your Streamlit dashboard")
        print("3. Run with real reel data using: python app/cli.py refresh")
        print()

    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        print("\nMake sure GROQ_API_KEY is set in your .env file:")
        print("  GROQ_API_KEY=your_api_key_here")
        print()


if __name__ == "__main__":
    main()
