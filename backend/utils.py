from textblob import TextBlob

def analyze_sentiment(text: str) -> str:
    """
    Analyzes the sentiment of the input text and returns a label.
    """
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def detect_escalation(text: str, sentiment: str) -> bool:
    """
    Detects if the conversation should be escalated to a human based on 
    keywords or sustained negative sentiment.
    """
    escalation_keywords = [
        "human", "agent", "supervisor", "manager", "representative", 
        "talk to someone", "not helpful", "awful", "terrible", "sue"
    ]
    
    text_lower = text.lower()
    
    # Check for keywords
    if any(keyword in text_lower for keyword in escalation_keywords):
        return True
    
    # Check for extreme negative sentiment
    if sentiment == "Negative":
        analysis = TextBlob(text)
        if analysis.sentiment.polarity < -0.5:
            return True
            
    return False
