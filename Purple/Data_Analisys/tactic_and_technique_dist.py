# %%
import json
from pathlib import Path
from typing import List, Dict, Any
from Utils.jsun import load_json
from collections import Counter

current_path = Path(__file__)
base_path = current_path.parent
path = base_path / "logs/logs/hp_config_1/sessions.json"

data = load_json(Path(path))
command_session_lengths: List[int] = []

tactics_used = {}
techniques_used = {}

for session in data:
    for command in session.get("full_session", []):
        tactic = command.get("tactic", "")
        technique = command.get("technique", "")
        if tactic:
            if tactic not in tactics_used:
                tactics_used[tactic] = 0
            tactics_used[tactic] += 1
        if technique:
            if technique not in techniques_used:
                techniques_used[technique] = 0
            techniques_used[technique] += 1

# tactics used
print("Tactics used:")
for tactic, count in tactics_used.items():
    print(f" - {tactic}: {count}")

total_commands = sum(tactics_used.values())
tactics_percentages = {tactic: (count / total_commands) * 100 for tactic, count in tactics_used.items()}
print("\nTactics used percentages:")
for tactic, percentage in tactics_percentages.items():
    print(f" - {tactic}: {percentage:.2f}%")


# techniques used
print("Techniques used:")
for technique, count in techniques_used.items():
    print(f" - {technique}: {count}")

total_techniques = sum(techniques_used.values())
techniques_percentages = {technique: (count / total_techniques) * 100 for technique, count in techniques_used.items()}
print("\nTechniques used percentages:")
for technique, percentage in techniques_percentages.items():
    print(f" - {technique}: {percentage:.2f}%")
# %%


