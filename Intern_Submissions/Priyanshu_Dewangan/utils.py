"""
Utility functions for audit logging and data management
"""

import json
import os
from datetime import datetime

AUDIT_LOG_FILE = "human_audit_log.json"


def load_audit_log():
    """Load audit log from file"""
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_audit_log(audit_log):
    """Save audit log to file"""
    with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(audit_log, f, indent=2, ensure_ascii=False)


def add_audit_entry(query, answer, confidence, source_chapter, status, correction=""):
    """Add single entry to audit log"""
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "answer": answer,
        "confidence": confidence,
        "source_chapter": source_chapter,
        "status": status,
        "human_correction": correction
    }
    
    audit_log = load_audit_log()
    audit_log.append(entry)
    save_audit_log(audit_log)
    
    return entry


def get_audit_stats():
    """Get statistics from audit log"""
    audit_log = load_audit_log()
    
    if not audit_log:
        return {
            "total": 0,
            "auto_approved": 0,
            "human_verified": 0,
            "human_corrected": 0,
            "no_answer": 0
        }
    
    return {
        "total": len(audit_log),
        "auto_approved": sum(1 for log in audit_log if log.get("status") == "AUTO_APPROVED"),
        "human_verified": sum(1 for log in audit_log if log.get("status") == "HUMAN_VERIFIED"),
        "human_corrected": sum(1 for log in audit_log if log.get("status") == "HUMAN_CORRECTED"),
        "no_answer": sum(1 for log in audit_log if log.get("status") == "NO_ANSWER_FOUND")
    }


def export_audit_log_csv():
    """Export audit log to CSV format"""
    import pandas as pd
    
    audit_log = load_audit_log()
    if not audit_log:
        return None
    
    df = pd.DataFrame(audit_log)
    return df.to_csv(index=False)


def clear_audit_log():
    """Clear audit log (use with caution)"""
    save_audit_log([])
