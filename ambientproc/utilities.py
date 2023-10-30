import json

def load_config(path ="./ambientCFG.json"):
    with open(path) as f:
        config = json.load(f)
    return config