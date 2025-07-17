#%%

import os
import sys
import numpy as np
from pathlib import Path
# Add parent directory to sys.path to allow imports from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
import ipywidgets as widgets
from IPython.display import display
from Style import colors
import json
import pprint
import matplotlib.pyplot as plt

logs_path = Path(__file__).resolve().parent.parent.parent / "logs"
experiment_names = os.listdir(logs_path)[::-1]

dropdown = widgets.Dropdown(
    options=experiment_names,
    description="Pick an experiment to analyze:",
)

display(dropdown)

#%%

selected_experiment = dropdown.value
filter_empty_sessions = False
use_omni_sessions = True
print(f"Analyzing experiment {selected_experiment}")

from Utils.jsun import load_json
import numpy as np
from Purple.Data_analysis.metrics import measure_session_length, measure_mitre_distribution, \
    measure_entropy_session_length, measure_entropy_techniques, measure_entropy_tactics

path = logs_path / selected_experiment
configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]
configs = sorted(
    configs,
    key=lambda fn: int(Path(fn).stem.split('_')[-1])
)

session_file_name = "omni_sessions.json" if use_omni_sessions else "sessions.json"
sessions_list = [load_json(path / config / session_file_name) for config in configs if session_file_name in os.listdir(path / config)]

if filter_empty_sessions:
    new_sessions_list = []
    for config_sessions in sessions_list:
        new_sessions_list.append([session for session in config_sessions if session["session"]])
    sessions_list = new_sessions_list

reconfig_indices = np.cumsum([len(session) for session in sessions_list][:-1])
combined_sessions = sum(sessions_list, [])
print(f"Reconfig indices: {reconfig_indices}")
print(f"Number of sessions: {len(combined_sessions)}")


length_data = measure_session_length(combined_sessions)
mitre_dist_data = measure_mitre_distribution(combined_sessions)

entropy_tactics_data = measure_entropy_tactics(combined_sessions)
session_entropy_tactics_data = [measure_entropy_tactics(session) for session in sessions_list]

entropy_techniques_data = measure_entropy_techniques(combined_sessions)
session_entropy_techniques_data = [measure_entropy_techniques(session) for session in sessions_list]

entropy_session_length_data = measure_entropy_session_length(combined_sessions)
session_entropy_session_length_data = [measure_entropy_session_length(session) for session in sessions_list]


#%% Plotting cumulative attack of unique techniqes vs sessions
plt.figure(figsize=(12, 6))
plt.plot(mitre_dist_data["session_cum_num_techniques"], marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Cumulative sum of unique techniques")
plt.xlabel("Session")
plt.ylabel("Number of Unique techniques")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()

print(np.max(mitre_dist_data["session_cum_num_techniques"]))

# %%

plt.figure(figsize=(12, 6))
plt.plot(mitre_dist_data["session_num_techniques"],
    marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Number of Unique Techniques per Session")
plt.xlabel("Session")
plt.ylabel("Number of Unique Techniques")
for index in reconfig_indices[0:10]:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
plt.legend()
plt.show()

# %% Session length

plt.figure(figsize=(12, 6))
plt.bar(range(len(length_data["session_lengths"])), length_data["session_lengths"])
plt.title("Session length per Session")
plt.xlabel("Session")
plt.ylabel("Session length")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
plt.legend()
plt.show()

# %% Tokens vs session

tokens_list = [load_json(path / config / "tokens_used.json") for config in configs]
token_reconfig_indices= np.cumsum([len(tokens) for tokens in tokens_list][:-1])
combined_tokens = sum(tokens_list, [])

prompt_tokens = [tokens["prompt_tokens"] for tokens in combined_tokens]
cached_tokens = [tokens["cached_tokens"] for tokens in combined_tokens]
completion_tokens = [tokens["completion_tokens"] for tokens in combined_tokens]

plt.figure(figsize=(12, 6))
plt.bar(range(len(prompt_tokens)), prompt_tokens,label="prompt tokens")
# plt.bar(range(len(cached_tokens)), prompt_tokens,label="cached tokens")
plt.bar(range(len(completion_tokens)), completion_tokens, label="completion tokens")
plt.title("Tokens per Session")
plt.xlabel("Session")
plt.ylabel("Session length")

for index in token_reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

# plt.grid()
plt.ylim(bottom=0)
plt.legend()
plt.show()

# %%

tactics = list(mitre_dist_data["tactics"].keys())
techniques = list(mitre_dist_data["tactics"].keys())

print(mitre_dist_data["tactics_heatmap"])

plt.figure(figsize=(15, 20))
plt.imshow(mitre_dist_data["tactics_heatmap"])
plt.xlabel("Session")
plt.ylabel("Tactic")
plt.yticks(range(len(tactics)), tactics)

# %%

tactics = list(mitre_dist_data["techniques"].keys())
techniques = list(mitre_dist_data["techniques"].keys())

print(mitre_dist_data["techniques_heatmap"])

plt.figure(figsize=(15, 20))
plt.imshow(mitre_dist_data["techniques_heatmap"])
plt.xlabel("Session")
plt.ylabel("Technique")
plt.yticks(range(len(tactics)), tactics)

# %%

import matplotlib.pyplot as plt

# your data
tactics = list(mitre_dist_data["tactics"].keys())
values  = list(mitre_dist_data["tactics"].values())

plt.figure(figsize=(10, 5))
bars = plt.bar(range(len(tactics)), values)
plt.xticks(range(len(tactics)), tactics, rotation=70)

# add value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,  # x position: center of the bar
        height,                           # y position: top of the bar
        f'{height}',                      # label text
        ha='center',                      # horizontal alignment
        va='bottom'                       # vertical alignment
    )

plt.tight_layout()
plt.show()


#%% Plotting entropy of techniques

entropies = [list(result["entropies"]) for result in session_entropy_techniques_data]
entropies = sum(entropies, [])

plt.figure(figsize=(12, 6))
plt.plot(entropies, marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Config entropy")
plt.xlabel("Session")
plt.ylabel("Entropy of unique techniques")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()
# %%

# Simple moving average
def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

eps = 5e-3
window_size = 2
smoothed = moving_average(entropy_techniques_data["entropies"], window_size)
diffs = np.abs(np.diff(smoothed, prepend=np.ones((window_size,)) * np.inf))

plt.figure(figsize=(12, 6))
plt.plot(entropy_techniques_data["entropies"], marker="", linestyle="-", c=colors.scheme[0])
plt.plot(diffs, marker="", linestyle="-", c=colors.scheme[1])
plt.scatter(np.arange(len(diffs))[diffs >= eps], entropy_techniques_data["entropies"][diffs >= eps], c=colors.scheme[0])
plt.scatter(np.arange(len(diffs))[diffs < eps], entropy_techniques_data["entropies"][diffs < eps], c=colors.scheme[-1])
plt.title("Experiment entropy of unique techniques")
plt.xlabel("Session")
plt.ylabel("Entropy of unique techniques")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()

# %% Entropy tactics all session

plt.figure(figsize=(12, 6))
plt.plot(entropy_tactics_data["entropies"], marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Experiment entropy of unique tactics")
plt.xlabel("Session")
plt.ylabel("Entropy of unique tactics")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()


#%% Plotting entropy of techniques every config

entropies = [list(result["entropies"]) for result in session_entropy_tactics_data]
entropies = sum(entropies, [])

plt.figure(figsize=(12, 6))
plt.plot(entropies, marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Config entropy")
plt.xlabel("Session")
plt.ylabel("Entropy of unique tactics")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()

# %%


#%% Plotting entropy of session length

entropies = [list(result["entropies"]) for result in session_entropy_session_length_data]
entropies = sum(entropies, [])

plt.figure(figsize=(12, 6))
plt.plot(entropies, marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Config entropy of session length")
plt.xlabel("Session")
plt.ylabel("Entropy of session length")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()
# %%
plt.figure(figsize=(12, 6))
plt.plot(entropy_session_length_data["entropies"], marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Experiment entropy of session length")
plt.xlabel("Session")
plt.ylabel("Entropy of session length")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()
# %%
