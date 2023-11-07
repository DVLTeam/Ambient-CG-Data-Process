import json

def load_config(path ="./ambientCFG.json"):
    with open(path) as f:
        config = json.load(f)

    print("Loaded config from: " + path)
    print(config)
    return config