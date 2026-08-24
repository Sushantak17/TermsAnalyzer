"""Download datasets for TermsAnalyzer.

Fetches two data sources:
1. TOS_Dataset from HuggingFace — clause-level fairness labels for training
2. ToS;DR annotated cases — real-world flagged clauses for RAG explanations
"""

import json
import os
import time
import requests
from pathlib import Path
from datasets import load_dataset


DATA_DIR = Path(__file__).parent
RAW_DIR = DATA_DIR / "raw"


def download_training_data():
    """Fetch TOS_Dataset from HuggingFace and save locally."""
    print("[1/2] Downloading TOS_Dataset from HuggingFace...")
    ds = load_dataset("CodeHima/TOS_DatasetV3")

    # inspect the dataset structure
    print(f"  Splits: {list(ds.keys())}")
    for split in ds:
        print(f"  {split}: {len(ds[split])} samples")
        print(f"  Columns: {ds[split].column_names}")
        print(f"  Example: {ds[split][0]}")

    # save each split as JSON
    out_dir = RAW_DIR / "tos_dataset"
    out_dir.mkdir(parents=True, exist_ok=True)

    for split in ds:
        records = [dict(row) for row in ds[split]]
        path = out_dir / f"{split}.json"
        with open(path, "w") as f:
            json.dump(records, f, indent=2)
        print(f"  Saved {len(records)} records to {path}")

    return ds


def download_tosdr_data():
    """Fetch annotated cases from ToS;DR API for RAG knowledge base."""
    print("\n[2/2] Fetching ToS;DR data for RAG knowledge base...")

    cases = []
    base_url = "https://api.tosdr.org/service/v1/"

    # fetch services page by page, extract their annotated points
    for page in range(1, 15):
        try:
            resp = requests.get(base_url, params={"page": page}, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            services = data.get("parameters", {}).get("services", [])
            if not services:
                print(f"  Page {page}: no more services, stopping.")
                break

            for svc in services:
                svc_name = svc.get("name", "Unknown")
                rating = svc.get("rating", {}).get("letter", "N/A")
                points = svc.get("points", [])

                for pt in points:
                    # only keep approved points with actual text
                    if pt.get("status") != "approved":
                        continue

                    case_data = pt.get("case", {})
                    quote = pt.get("quoteText", "").strip()
                    title = pt.get("title", case_data.get("title", ""))

                    if not title and not quote:
                        continue

                    cases.append({
                        "clause_text": quote if quote else title,
                        "title": title,
                        "company": svc_name,
                        "company_rating": rating,
                        "classification": case_data.get("classification", "neutral"),
                        "category": case_data.get("topic", {}).get("title", "General"),
                        "explanation": case_data.get("description", title),
                    })

            print(f"  Page {page}: found {len(services)} services, {len(cases)} total cases so far")
            time.sleep(0.5)  # be nice to the API

        except Exception as e:
            print(f"  Page {page}: API error ({e}), stopping.")
            break

    # if API didn't return enough, load curated fallback
    if len(cases) < 50:
        print(f"  Only got {len(cases)} cases from API, adding curated fallback...")
        cases.extend(get_curated_fallback())

    # deduplicate by clause text
    seen = set()
    unique = []
    for c in cases:
        key = c["clause_text"][:100].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # save
    out_path = RAW_DIR / "tosdr_cases.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(unique, f, indent=2)
    print(f"  Saved {len(unique)} unique cases to {out_path}")

    return unique


def get_curated_fallback():
    """Hand-picked ToS;DR annotations for when the API is unreliable."""
    return [
        {
            "clause_text": "The service can share your personal information with third parties",
            "title": "Third-party sharing of personal data",
            "company": "Facebook",
            "company_rating": "E",
            "classification": "bad",
            "category": "Third-Party Sharing",
            "explanation": "Your personal data may be shared with advertisers and partners without granular consent"
        },
        {
            "clause_text": "This service tracks you on other websites",
            "title": "Tracks you on other websites",
            "company": "Google",
            "company_rating": "C",
            "classification": "bad",
            "category": "Tracking",
            "explanation": "The service uses cookies and tracking pixels to monitor your activity across the web"
        },
        {
            "clause_text": "You waive your right to a class action lawsuit",
            "title": "Mandatory arbitration clause",
            "company": "Amazon",
            "company_rating": "D",
            "classification": "blocker",
            "category": "Arbitration",
            "explanation": "Users cannot join class actions and must resolve disputes through binding arbitration"
        },
        {
            "clause_text": "By using the service, you grant us a worldwide, royalty-free license to use your content",
            "title": "Broad content license",
            "company": "Instagram",
            "company_rating": "D",
            "classification": "bad",
            "category": "Content Rights",
            "explanation": "The platform gets extensive rights to use, modify, and distribute your uploaded content"
        },
        {
            "clause_text": "The service may change the terms at any time without notice",
            "title": "Terms can change without notice",
            "company": "Snapchat",
            "company_rating": "D",
            "classification": "blocker",
            "category": "Terms Changes",
            "explanation": "The company can modify the agreement unilaterally without notifying users"
        },
        {
            "clause_text": "You can request access to your personal data",
            "title": "Right to access your data",
            "company": "DuckDuckGo",
            "company_rating": "A",
            "classification": "good",
            "category": "Data Access",
            "explanation": "Users have the right to obtain a copy of the personal data held about them"
        },
        {
            "clause_text": "Your account can be deleted at any time without prior notice or explanation",
            "title": "Account terminated without warning",
            "company": "Twitter",
            "company_rating": "E",
            "classification": "blocker",
            "category": "Account Suspension",
            "explanation": "The service can terminate accounts unilaterally, potentially losing all user data"
        },
        {
            "clause_text": "The service collects your location data even when the app is not in use",
            "title": "Background location tracking",
            "company": "Uber",
            "company_rating": "D",
            "classification": "bad",
            "category": "Tracking",
            "explanation": "Location data is collected continuously, not just during active use of the service"
        },
        {
            "clause_text": "We will notify you 30 days in advance before making changes to the terms",
            "title": "Advance notice of terms changes",
            "company": "Mozilla Firefox",
            "company_rating": "A",
            "classification": "good",
            "category": "Terms Changes",
            "explanation": "Users are given adequate time to review changes before they take effect"
        },
        {
            "clause_text": "Your data is encrypted in transit and at rest",
            "title": "Data encrypted in transit and at rest",
            "company": "Signal",
            "company_rating": "A",
            "classification": "good",
            "category": "Data Security",
            "explanation": "Strong encryption protects user data both during transmission and while stored"
        },
        {
            "clause_text": "The service retains your data even after you delete your account",
            "title": "Data retained after account deletion",
            "company": "TikTok",
            "company_rating": "E",
            "classification": "bad",
            "category": "Data Retention",
            "explanation": "Deleting your account does not guarantee that all your data is actually removed"
        },
        {
            "clause_text": "We may use your content to train machine learning models",
            "title": "Content used for AI training",
            "company": "Reddit",
            "company_rating": "D",
            "classification": "bad",
            "category": "Content Rights",
            "explanation": "User-generated content may be used to improve AI models without explicit consent"
        },
        {
            "clause_text": "You can delete your data at any time and it will be permanently removed",
            "title": "Right to delete data permanently",
            "company": "ProtonMail",
            "company_rating": "A",
            "classification": "good",
            "category": "Data Deletion",
            "explanation": "Users can fully and permanently erase their personal data from the service"
        },
        {
            "clause_text": "The service may sell or transfer your personal data in case of a merger or acquisition",
            "title": "Data transferred during acquisition",
            "company": "LinkedIn",
            "company_rating": "C",
            "classification": "bad",
            "category": "Third-Party Sharing",
            "explanation": "In a corporate transaction, user data is treated as a business asset and transferred"
        },
        {
            "clause_text": "This service limits its liability to the maximum extent permitted by law",
            "title": "Broad liability limitation",
            "company": "Netflix",
            "company_rating": "C",
            "classification": "bad",
            "category": "Liability",
            "explanation": "The company minimizes its financial responsibility for damages or losses you may incur"
        },
        {
            "clause_text": "The service does not sell your personal data to third parties",
            "title": "No sale of personal data",
            "company": "Apple",
            "company_rating": "B",
            "classification": "good",
            "category": "Third-Party Sharing",
            "explanation": "The company commits to not selling user data as a revenue stream"
        },
        {
            "clause_text": "We may use cookies and similar technologies to collect information about your browsing behavior",
            "title": "Cookie-based tracking",
            "company": "Yahoo",
            "company_rating": "D",
            "classification": "bad",
            "category": "Tracking",
            "explanation": "Browsing activity is monitored through cookies for profiling and advertising"
        },
        {
            "clause_text": "Children under 13 may not use this service",
            "title": "Age restriction enforced",
            "company": "YouTube",
            "company_rating": "D",
            "classification": "neutral",
            "category": "Children's Privacy",
            "explanation": "The service sets a minimum age to comply with COPPA regulations"
        },
        {
            "clause_text": "You agree to indemnify and hold the service harmless from any claims arising from your use",
            "title": "User indemnification required",
            "company": "Airbnb",
            "company_rating": "D",
            "classification": "bad",
            "category": "Liability",
            "explanation": "Users bear financial responsibility for legal claims related to their use of the service"
        },
        {
            "clause_text": "The service provides a transparency report about government data requests",
            "title": "Transparency report published",
            "company": "Microsoft",
            "company_rating": "B",
            "classification": "good",
            "category": "Government Requests",
            "explanation": "The company publicly discloses how often governments request user data"
        },
        {
            "clause_text": "We collect data about the device you use, including hardware model, operating system, and unique identifiers",
            "title": "Device fingerprinting",
            "company": "Spotify",
            "company_rating": "C",
            "classification": "bad",
            "category": "Tracking",
            "explanation": "Detailed device information is collected, enabling user identification across sessions"
        },
        {
            "clause_text": "Your content will be deleted within 30 days of account closure",
            "title": "Timely data deletion after account closure",
            "company": "Dropbox",
            "company_rating": "B",
            "classification": "good",
            "category": "Data Deletion",
            "explanation": "The service commits to a specific timeline for removing user data after account deletion"
        },
        {
            "clause_text": "The service may use automated decision-making including profiling that significantly affects you",
            "title": "Automated profiling with significant effects",
            "company": "PayPal",
            "company_rating": "D",
            "classification": "bad",
            "category": "Automated Decisions",
            "explanation": "Algorithmic decisions may impact your access to services without human review"
        },
        {
            "clause_text": "You own all rights to the content you post on this service",
            "title": "Users retain content ownership",
            "company": "WordPress.com",
            "company_rating": "B",
            "classification": "good",
            "category": "Content Rights",
            "explanation": "The platform does not claim ownership over user-created content"
        },
        {
            "clause_text": "The service shares data with law enforcement without a warrant when they believe it is necessary",
            "title": "Data shared with law enforcement without warrant",
            "company": "Zoom",
            "company_rating": "D",
            "classification": "blocker",
            "category": "Government Requests",
            "explanation": "User data may be disclosed to authorities without proper legal process"
        },
        {
            "clause_text": "We will only keep your personal data for as long as necessary for the purposes described",
            "title": "Limited data retention period",
            "company": "Brave Browser",
            "company_rating": "A",
            "classification": "good",
            "category": "Data Retention",
            "explanation": "Data is not stored indefinitely — it is deleted when no longer needed"
        },
        {
            "clause_text": "By using the service you consent to receiving promotional emails and messages",
            "title": "Implied consent to marketing",
            "company": "Wish",
            "company_rating": "E",
            "classification": "bad",
            "category": "Marketing",
            "explanation": "Users are automatically opted into marketing communications by using the service"
        },
        {
            "clause_text": "The service allows you to export all your data in a machine-readable format",
            "title": "Data portability supported",
            "company": "Mastodon",
            "company_rating": "A",
            "classification": "good",
            "category": "Data Access",
            "explanation": "Users can download their complete data for transfer to another service"
        },
        {
            "clause_text": "This service uses your personal data for targeted advertising",
            "title": "Personal data used for targeted ads",
            "company": "Pinterest",
            "company_rating": "D",
            "classification": "bad",
            "category": "Advertising",
            "explanation": "Personal information is leveraged to serve personalized advertisements"
        },
        {
            "clause_text": "You must be at least 16 years old to use this service in the European Union",
            "title": "GDPR age compliance",
            "company": "WhatsApp",
            "company_rating": "D",
            "classification": "neutral",
            "category": "Children's Privacy",
            "explanation": "The service complies with GDPR age of consent requirements for data processing"
        },
        {
            "clause_text": "The service requires you to use your real name",
            "title": "Real name required",
            "company": "Facebook",
            "company_rating": "E",
            "classification": "bad",
            "category": "Privacy",
            "explanation": "Forced real-name policies prevent anonymous use and increase privacy risks"
        },
        {
            "clause_text": "The service logs your IP address for every interaction",
            "title": "IP address logging",
            "company": "Cloudflare",
            "company_rating": "C",
            "classification": "bad",
            "category": "Tracking",
            "explanation": "IP addresses are recorded, which can be used to identify and track users"
        },
        {
            "clause_text": "This service is provided 'as is' without warranty of any kind",
            "title": "No warranty provided",
            "company": "GitHub",
            "company_rating": "B",
            "classification": "neutral",
            "category": "Liability",
            "explanation": "The service disclaims all warranties, which is standard but limits user recourse"
        },
        {
            "clause_text": "The service will fight to protect your data from government requests",
            "title": "Resists government data requests",
            "company": "Tutanota",
            "company_rating": "A",
            "classification": "good",
            "category": "Government Requests",
            "explanation": "The company will challenge overbroad or unjustified government requests for data"
        },
        {
            "clause_text": "Third-party analytics services are used to collect usage data",
            "title": "Third-party analytics tracking",
            "company": "Medium",
            "company_rating": "C",
            "classification": "bad",
            "category": "Tracking",
            "explanation": "External services like Google Analytics collect and process your usage patterns"
        },
        {
            "clause_text": "We may contact you via push notifications, SMS, or email about new features and promotions",
            "title": "Multi-channel promotional messaging",
            "company": "Tinder",
            "company_rating": "E",
            "classification": "bad",
            "category": "Marketing",
            "explanation": "The service reserves the right to send promotional messages across multiple channels"
        },
        {
            "clause_text": "Your data is stored on servers located in the European Union",
            "title": "EU data residency",
            "company": "OVHcloud",
            "company_rating": "B",
            "classification": "good",
            "category": "Data Security",
            "explanation": "Storing data in the EU provides stronger privacy protections under GDPR"
        },
        {
            "clause_text": "The service collects your contacts list and address book information",
            "title": "Contacts and address book collected",
            "company": "TikTok",
            "company_rating": "E",
            "classification": "blocker",
            "category": "Data Collection",
            "explanation": "The service accesses your personal contacts, which involves third-party privacy"
        },
        {
            "clause_text": "We use end-to-end encryption for all messages",
            "title": "End-to-end encryption for messages",
            "company": "Signal",
            "company_rating": "A",
            "classification": "good",
            "category": "Data Security",
            "explanation": "Messages can only be read by the sender and recipient, not even by the service"
        },
        {
            "clause_text": "Your personal data may be transferred to countries that do not have equivalent data protection laws",
            "title": "Data transferred to countries with weaker protections",
            "company": "Meta",
            "company_rating": "E",
            "classification": "bad",
            "category": "Data Security",
            "explanation": "International data transfers may expose your data to weaker privacy regimes"
        },
        {
            "clause_text": "The service respects Do Not Track signals from your browser",
            "title": "Honors Do Not Track",
            "company": "Brave Browser",
            "company_rating": "A",
            "classification": "good",
            "category": "Tracking",
            "explanation": "The service actively responds to browser privacy preferences"
        },
    ]


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # download training data
    ds = download_training_data()

    # download RAG knowledge base data
    cases = download_tosdr_data()

    print(f"\nDone! Training data and {len(cases)} RAG cases saved to {RAW_DIR}/")
