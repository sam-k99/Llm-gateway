import re

def redact_pii(text: str) -> str:
    """
    Scans text for PII (SSN, Emails) and replaces it with [REDACTED].
    """
    # Redact Emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[REDACTED_EMAIL]', text)
    
    # Redact SSNs (format: XXX-XX-XXXX or XXXXXXXXX)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
    
    return text

def detect_prompt_injection(text: str) -> bool:
    """
    Scans text for basic prompt injection attacks.
    Returns True if an attack is detected.
    """
    injection_keywords = [
        "ignore previous instructions",
        "ignore all previous",
        "system prompt:",
        "reveal your initial",
        "drop table",
        "delete from"
    ]
    
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in injection_keywords):
        return True
        
    return False
