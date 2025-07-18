from typing import Dict, List, Any
from Purple.Data_analysis.metrics import measure_mitre_distribution
from Style import colors

import matplotlib.pyplot as plt

def plot_heatmaps(sessions: List[Dict[str, Any]], reconfig_indices: List[int]):
    mitre_dist_data = measure_mitre_distribution(sessions)

    tactics = list(mitre_dist_data["tactics"].keys())
    techniques = list(mitre_dist_data["techniques"].keys())

    plt.figure(figsize=(15, 20))
    plt.imshow(mitre_dist_data["tactics_heatmap"])
    plt.xlabel("Session")
    plt.ylabel("Tactic")
    plt.yticks(range(len(tactics)), tactics)
    plt.show()

    plt.figure(figsize=(15, 20))
    plt.imshow(mitre_dist_data["techniques_heatmap"])
    plt.xlabel("Session")
    plt.ylabel("Technique")
    plt.yticks(range(len(techniques)), techniques)
    plt.show()
