from typing import Dict, List, Any
from Purple.Data_analysis.metrics import measure_entropy_tactics, \
    measure_entropy_techniques, measure_entropy_session_length
from Style import colors

import matplotlib.pyplot as plt

def plot_entropy(combined_sessions: List[Dict[str, Any]],
        sessions_list: List[List[Dict[str, Any]]], reconfig_indices: List[int]):
    
    tactics_entropy_data = measure_entropy_tactics(combined_sessions)
    tactics_entropy_data_list = [measure_entropy_tactics(session) for session in sessions_list]

    techniques_entropy_data = measure_entropy_techniques(combined_sessions)
    techniques_entropy_data_list = [measure_entropy_techniques(session) for session in sessions_list]

    session_length_entropy_data = measure_entropy_session_length(combined_sessions)
    session_length_entropy_data_list = [measure_entropy_session_length(session) for session in sessions_list]

    for entropy_data, entropy_data_list in zip(
                ["tactics", "techniques", "session length"]
                [tactics_entropy_data, techniques_entropy_data, session_length_entropy_data],
                [tactics_entropy_data_list, techniques_entropy_data_list, session_length_entropy_data_list]
            ):
        entropies = [list(result["entropies"]) for result in entropy_data_list]
        entropies = sum(entropies, [])

        plt.figure(figsize=(12, 6))
        plt.plot(entropies, marker="o", linestyle="-", c=colors.scheme[0])
        plt.title("Config entropy")
        plt.xlabel("Session")
        plt.ylabel("Entropy of unique tactics")

        for index in reconfig_indices:
            plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

        plt.ylim(bottom=0)
        plt.legend()
        plt.show()

        plt.plot(entropy_data["entropies"], marker="o", linestyle="-", c=colors.scheme[0])
        plt.title("Entropy of session length")
        plt.xlabel("Session")
        plt.ylabel("Entropy of session length")

        for index in reconfig_indices:
            plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

        plt.ylim(bottom=0)
        plt.legend()
        plt.show()