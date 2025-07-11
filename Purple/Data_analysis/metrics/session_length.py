import numpy as np
from typing import Dict, List, Any
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