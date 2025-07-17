from typing import Dict, List, Any
from Purple.Data_analysis.metrics import measure_session_length
from Style import colors

import matplotlib.pyplot as plt

def plot_session_length(sessions: List[Dict[str, Any]], reconfig_indices: List[int]):
    length_data = measure_session_length(sessions)

    plt.figure(figsize=(12, 6))
    plt.plot(length_data["session_lengths"], color=colors.scheme[0])
    plt.title("Session length per Session")
    plt.xlabel("Session")
    plt.ylabel("Session length")

    for index in reconfig_indices:
        plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

    plt.ylim(bottom=0)
    plt.legend()
    plt.show()

