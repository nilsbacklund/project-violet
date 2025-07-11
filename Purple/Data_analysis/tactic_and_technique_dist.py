# %%
import json
from pathlib import Path
from typing import List, Dict, Any
from Utils.jsun import load_json
from collections import Counter

current_path = Path(__file__)
base_path = current_path.parent
path = base_path / "logs/experiment_2025-07-10T22_03_01/hp_config_1/sessions.json"

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
for tactic, count in sorted(tactics_used.items(), key=lambda x: x[1], reverse=True):
    print(f" - {tactic}: {count}")

total_commands = sum(tactics_used.values())
tactics_percentages = {tactic: (count / total_commands) * 100 for tactic, count in tactics_used.items()}
print("\nTactics used percentages:")
for tactic, percentage in sorted(tactics_percentages.items(), key=lambda x: x[1], reverse=True):
    print(f" - {tactic}: {percentage:.2f}%")


# techniques used
print("\nTechniques used:")
for technique, count in sorted(techniques_used.items(), key=lambda x: x[1], reverse=True):
    print(f" - {technique}: {count}")

total_techniques = sum(techniques_used.values())
techniques_percentages = {technique: (count / total_techniques) * 100 for technique, count in techniques_used.items()}
print("\nTechniques used percentages:")
for technique, percentage in sorted(techniques_percentages.items(), key=lambda x: x[1], reverse=True):
    print(f" - {technique}: {percentage:.2f}%")
# %%


