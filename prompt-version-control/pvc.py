import json
from typing import Dict, Any

class PromptVersionControl:
    def __init__(self):
        self.versions: Dict[str, Dict[str, Any]] = {}

    def register_prompt(self, name: str, version: str, template: str, author: str):
        key = f"{name}:{version}"
        self.versions[key] = {
            "name": name,
            "version": version,
            "template": template,
            "author": author
        }

    def get_prompt(self, name: str, version: str) -> Dict[str, Any]:
        key = f"{name}:{version}"
        return self.versions.get(key, {"error": "Prompt version not found"})

if __name__ == "__main__":
    pvc = PromptVersionControl()
    pvc.register_prompt("rag_system_prompt", "v1.0", "You are a helpful assistant. Use context: {context}", "Engineering Team")
    pvc.register_prompt("rag_system_prompt", "v1.1", "You are a strict technical expert. Only answer from {context}", "AI Team")

    print("Fetched Prompt:", json.dumps(pvc.get_prompt("rag_system_prompt", "v1.1"), indent=2))
