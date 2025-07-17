from typing import Dict, List, Any
from Purple.Data_analysis.metrics import measure_mitre_distribution
from Style import colors

import matplotlib.pyplot as plt

def plot_mitre_data(sessions: List[Dict[str, Any]], reconfig_indices: List[int]):
    mitre_dist_data = measure_mitre_distribution(sessions)

    for name in ["tactics", "techniques"]:
        plt.figure(figsize=(12, 6))
        plt.plot(mitre_dist_data[f"session_cum_num_{name}"], marker="o", linestyle="-", c=colors.scheme[0])
        plt.title(f"Cumulative sum of unique {name}")
        plt.xlabel("Session")
        plt.ylabel(f"Number of unique {name}")

        for index in reconfig_indices:
            plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

        plt.ylim(bottom=0)
        plt.legend()
        plt.show()
        plt.figure(figsize=(12, 6))

        plt.plot(mitre_dist_data[f"session_num_{name}"],
            marker="o", linestyle="-", c=colors.scheme[0])
        plt.title(f"Number of unique {name} per session")
        plt.xlabel("Session")
        plt.ylabel(f"Number of unique {name}")
        for index in reconfig_indices[0:10]:
            plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

        plt.ylim(bottom=0)
        plt.legend()
        plt.show()
