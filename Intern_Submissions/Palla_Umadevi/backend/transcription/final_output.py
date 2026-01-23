import json

def save_final(data, path="final_output.json"):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
