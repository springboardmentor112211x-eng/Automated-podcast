import json

def save_final(topics, path="final_output.json"):
    with open(path, "w") as f:
        json.dump({
            "total_topics": len(topics),
            "topics": topics
        }, f, indent=2)
