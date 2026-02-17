from textblob import TextBlob

# Social Determinants of Health (SDOH) keyword mapping
SDOH_KEYWORDS = {
    "housing": ["rent", "evict", "homeless", "shelter", "apartment", "lease", "landlord"],
    "food": ["food", "hunger", "grocery", "meal", "starve", "nutrition", "eat"],
    "social": ["friend", "lonely", "isolation", "support", "community", "family", "group"],
    "employment": ["job", "work", "unemployed", "income", "paycheck", "boss", "hire"],
    "transport": ["bus", "transport", "commute", "car", "ride", "walk", "distance"],
    "healthcare": ["doctor", "clinic", "medicine", "treatment", "insurance", "hospital"],
    "violence": ["abuse", "violence", "assault", "crime", "police", "safety"],
    "education": ["school", "college", "education", "degree", "class", "teacher"],
    # Add more as needed
}

def analyze_narrative(text):
    """
    Analyze a narrative for sentiment and SDOH tags.
    Returns (sentiment_score, auto_tags)
    """
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity  # -1 (neg) to 1 (pos)
    tags = set()
    text_lc = text.lower()
    for tag, keywords in SDOH_KEYWORDS.items():
        if any(word in text_lc for word in keywords):
            tags.add(tag)
    return sentiment, list(tags)
