import re

SENSITIVE_PATTERNS = [
    r"\bpassword\b",
    r"\botp\b",
    r"\bupi\b",
    r"\bcredit card\b",
    r"\bapi key\b",
    r"\btoken\b",
]

def safety_check(text: str):
    flags = []
    for pat in SENSITIVE_PATTERNS:
        if re.search(pat, text.lower()):
            flags.append(pat)

    return {
        "is_safe": len(flags) == 0,
        "flags": flags,
        "action": "HUMAN_REVIEW" if flags else "AUTO_APPROVE"
    }
