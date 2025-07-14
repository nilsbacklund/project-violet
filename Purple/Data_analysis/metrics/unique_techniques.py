import numpy as np
from typing import Dict, List, Any, Set

def measure_unique_techniques(sessions: List[Dict]) -> Dict[str, Any]:
    config_techniques = set()
    session_techniques: List[Set] = []
    session_num_techniques: List[int] = []

    for session in sessions:
        current_techniques = str(session["techniques"]).split("--")
        current_techniques = { technique.split("-")[0].strip() for technique in current_techniques if technique != ""}
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