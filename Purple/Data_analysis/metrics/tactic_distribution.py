from typing import Dict, List, Any

def measure_tactic_distribution(sessions: List[Dict]) -> Dict[str, Any]:
    all_tactics = {}
    all_techniques = {}
    session_tactics = []
    session_techniques = []

    for session in sessions:
        current_tactics = {}
        current_techniques = {}
        for command in session.get("full_session", []):
            tactic = command.get("tactic", "")
            technique = command.get("technique", "")
            if tactic:
                if tactic not in all_tactics:
                    all_tactics[tactic] = 0
                if tactic not in current_tactics:
                    current_tactics[tactic] = 0
                all_tactics[tactic] += 1
                current_tactics[tactic] += 1
            if technique:
                if technique not in all_techniques:
                    all_techniques[technique] = 0
                if technique not in current_techniques:
                    current_techniques[technique] = 0
                all_techniques[technique] += 1
                current_techniques[technique] += 1
        session_tactics.append(current_tactics)
        session_techniques.append(current_techniques)

    all_tactics = { k: v for k, v in sorted(all_tactics.items(), key=lambda item: item[1], reverse=True)}
    all_techniques = { k: v for k, v in sorted(all_techniques.items(), key=lambda item: item[1], reverse=True)}

    total_tactics = sum(all_tactics.values())
    tactics_frac = {tactic: (count / total_tactics) for tactic, count in all_tactics.items()}
    tactics_frac = dict(sorted(tactics_frac.items(), key=lambda item: item[1], reverse=True))
    
    total_techniques = sum(all_techniques.values())
    techniques_frac = {technique: (count / total_techniques) for technique, count in all_techniques.items()}
    techniques_frac = dict(sorted(techniques_frac.items(), key=lambda item: item[1], reverse=True))

    assert abs(sum(tactics_frac.values()) - 1) < 1e-5
    assert abs(sum(techniques_frac.values()) - 1) < 1e-5

    results = {
        "tactics": all_tactics,
        "techniques": all_techniques,
        "tactics_frac": tactics_frac,
        "techniques_frac": techniques_frac,
        "session_tactics": session_tactics,
        "session_techniques": session_techniques,
    }

    return results