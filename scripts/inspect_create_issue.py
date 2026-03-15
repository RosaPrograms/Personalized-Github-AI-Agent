import json
import pathlib

from src.agents import CoordinatorAgent

if __name__ == "__main__":
    d = json.loads(pathlib.Path('.draft.json').read_text())
    result = CoordinatorAgent().create_issue_from_draft(d['draft'])
    print(result)
