from typing import Dict, List, Any

def measure_tactic_distribution(sessions: List[Dict]) -> Dict[str, Any]:
    tactics_used = {}
    techniques_used = {}

    for session in sessions:
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

    tactics_used = { k: v for k, v in sorted(tactics_used.items(), key=lambda item: item[1], reverse=True)}
    techniques_used = { k: v for k, v in sorted(techniques_used.items(), key=lambda item: item[1], reverse=True)}

    total_commands = sum(tactics_used.values())
    tactics_frac = {tactic: (count / total_commands) for tactic, count in tactics_used.items()}
    total_techniques = sum(techniques_used.values())
    techniques_frac = {technique: (count / total_techniques) for technique, count in techniques_used.items()}

    assert abs(sum(tactics_frac.values()) - 1) < 1e-5
    assert abs(sum(techniques_frac.values()) - 1) < 1e-5

    results = {
        "tactics": tactics_used,
        "techniques": techniques_used,
        "tactics_frac": tactics_frac,
        "techniques_frac": techniques_frac,
    }

    return results