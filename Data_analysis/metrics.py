import numpy as np
from typing import Dict, List, Any, Set
from collections import Counter

def measure_session_length(sessions: List[Dict]) -> Dict[str, Any]:
    session_lengths = [session.get("length", 0) for session in sessions]
    session_lengths = np.array(session_lengths)

    mean_length = session_lengths.mean()
    var_length = session_lengths.var()
    std_length = session_lengths.std()
    min_length = session_lengths.min()
    max_length = session_lengths.max()
    range_length = max_length - min_length
    q1 = np.percentile(session_lengths, 25)
    median_length = np.percentile(session_lengths, 50)
    q3 = np.percentile(session_lengths, 75)

    length_counts = Counter(session_lengths)
    five_most_common = length_counts.most_common(5)

    results = {
        "mean": mean_length,
        "var": var_length,
        "std": std_length,
        "min": min_length,
        "max": max_length,
        "range": range_length,
        "median": median_length,
        "q1": q1,
        "q3": q3,
        "middle_range": q3 - q1,
        "five_most_common": five_most_common,
    }
    results = { key:float(value) if key != "five_most_common" else [(int(pair[0]), pair[1]) for pair in value] for key, value in results.items()}
    results["session_lengths"] = session_lengths
    return results

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

    total_commands = sum(tactics_used.values())
    tactics_frac = {tactic: (count / total_commands) for tactic, count in tactics_used.items()}
    total_techniques = sum(techniques_used.values())
    techniques_frac = {technique: (count / total_techniques) for technique, count in techniques_used.items()}

    assert sum(tactics_frac.values()) == 1
    assert sum(techniques_frac.values()) == 1

    results = {
        "tactics": tactics_used,
        "techniques": techniques_used,
        "tactics_frac": tactics_frac,
        "techniques_frac": techniques_frac,
    }

    return results

def measure_unique_techniques(sessions: List[Dict]) -> Dict[str, Any]:
    config_techniques = set()
    session_techniques: List[Set] = []
    session_num_techniques: List[int] = []

    for session in sessions:
        current_techniques = str(session["techniques"]).split("--")
        current_techniques = set([technique.split("-")[0].strip() for technique in current_techniques])
        config_techniques.update(current_techniques)
        session_techniques.append(current_techniques)
        session_num_techniques.append(len(current_techniques))

    session_cum_num_techniques = [int(num) for num in np.cumsum(session_num_techniques)]

    results = {
        "config_num_techniques": len(config_techniques),
        "config_techniques": config_techniques,
        "session_techniques": session_techniques,
        "session_num_techniques": session_num_techniques,
        "session_cum_num_techniques": session_cum_num_techniques,
    }

    return results