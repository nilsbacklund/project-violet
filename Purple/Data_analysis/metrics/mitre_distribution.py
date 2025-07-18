from typing import Dict, List, Any
import numpy as np

def create_heatmap(rows: List[str], data: List[Dict[str, int]]) -> np.ndarray:
    rows_to_num = { row:i for i, row in enumerate(rows)}
    heatmap = np.zeros((len(rows), len(data)))

    for i, session in enumerate(data):
        for row, freq in session.items():
            heatmap[rows_to_num[row], i] = freq

    return heatmap

def measure_mitre_distribution(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_tactics = {}
    all_techniques = {}
    session_tactics = []
    session_techniques = []

    session_num_tactics: List[int] = []
    session_cum_num_tactics: List[int] = []

    session_num_techniques: List[int] = []
    session_cum_num_techniques: List[int] = []

    for session in sessions:
        current_tactics = {}
        current_techniques = {}
        new_techniques_count = 0
        new_tactics_count = 0

        for command in session.get("full_session", []):
            tactic = command.get("tactic", "")
            technique = command.get("technique", "")
            if tactic:
                if tactic not in all_tactics:
                    all_tactics[tactic] = 0
                    new_tactics_count += 1
                if tactic not in current_tactics:
                    current_tactics[tactic] = 0
                all_tactics[tactic] += 1
                current_tactics[tactic] += 1
            if technique:
                if technique not in all_techniques:
                    all_techniques[technique] = 0
                    new_techniques_count += 1
                if technique not in current_techniques:
                    current_techniques[technique] = 0
                all_techniques[technique] += 1
                current_techniques[technique] += 1

        session_tactics.append(current_tactics)
        session_techniques.append(current_techniques)

        session_num_tactics.append(new_tactics_count)
        session_cum_num_tactics.append(len(all_tactics))

        session_num_techniques.append(new_techniques_count)
        session_cum_num_techniques.append(len(all_techniques))

    all_tactics = { k: v for k, v in sorted(all_tactics.items(), key=lambda item: item[1], reverse=True)}
    all_techniques = { k: v for k, v in sorted(all_techniques.items(), key=lambda item: item[1], reverse=True)}

    total_tactics = sum(all_tactics.values())
    tactics_frac = {tactic: (count / total_tactics) for tactic, count in all_tactics.items()}
    tactics_frac = dict(sorted(tactics_frac.items(), key=lambda item: item[1], reverse=True))
    
    total_techniques = sum(all_techniques.values())
    techniques_frac = {technique: (count / total_techniques) for technique, count in all_techniques.items()}
    techniques_frac = dict(sorted(techniques_frac.items(), key=lambda item: item[1], reverse=True))

    # Let's create a heatmap for funsies

    tactic_names = list(all_tactics.keys())
    technique_names = list(all_techniques.keys())
    tactics_heatmap = create_heatmap(tactic_names, session_tactics)
    techniques_heatmap = create_heatmap(technique_names, session_techniques)

    results = {
        "tactics": all_tactics,
        "techniques": all_techniques,
        "num_tactics": len(all_tactics),
        "num_techniques": len(all_techniques),
        "tactics_frac": tactics_frac,
        "techniques_frac": techniques_frac,
        "session_tactics": session_tactics,
        "session_techniques": session_techniques,
        "session_num_tactics": session_num_tactics,
        "session_cum_num_tactics": session_cum_num_tactics,
        "session_num_techniques": session_num_techniques,
        "session_cum_num_techniques": session_cum_num_techniques,
        "tactics_heatmap": tactics_heatmap,
        "techniques_heatmap": techniques_heatmap
    }

    return results