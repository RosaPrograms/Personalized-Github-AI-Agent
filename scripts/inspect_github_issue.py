import json
from src.tools import GitHubOps

with open('.draft.json','r') as f:
    draft = json.load(f)['draft']

ops = GitHubOps()
res = ops.create_issue(title=draft['title'], body=draft['description'], labels=draft.get('labels'))
print(res)
