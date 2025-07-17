#%%

import os
import sys
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
from Purple.RagData.retrive_techniques import retrieve_unique_techniques

logs_path = Path(__file__).resolve().parent.parent.parent / "logs"
experiment_names = [name for name in os.listdir(logs_path)[::-1] if str(name).startswith("experiment")]

dropdown = widgets.Dropdown(
    options=experiment_names,
    description="Pick an experiment to analyze:",
)

display(dropdown)

#%%

selected_experiment = dropdown.value
filter_empty_sessions = False
print(f"Analyzing experiment {selected_experiment}")

from Utils.jsun import load_json
import numpy as np
from Purple.Data_analysis.metrics import measure_session_length, \
    measure_tactic_distribution, measure_unique_techniques, \
    measure_entropy_session_length, measure_entropy_techniques

path = logs_path / selected_experiment
configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]
configs = sorted(
    configs,
    key=lambda fn: int(Path(fn).stem.split('_')[-1])
)

sessions_list = [load_json(path / config / "sessions.json") for config in configs if "sessions.json" in os.listdir(path / config)]

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
tactic_dist_data = measure_tactic_distribution(combined_sessions)
unique_techniques_data = measure_unique_techniques(combined_sessions)
entropy_techniques_data = measure_entropy_techniques(combined_sessions)
session_entropy_techniques_data = [measure_entropy_techniques(session) for session in sessions_list]

entropy_session_length_data = measure_entropy_session_length(combined_sessions)
session_entropy_session_length_data = [measure_entropy_session_length(session) for session in sessions_list]

# %% scrap code to see how big the difference is 
print("All techniques:")
attack_tech = [tactic.split(":") for tactic in tactic_dist_data["techniques"]]
attack_techs = []
for tactic in attack_tech:
    if len(tactic) > 1:
        attack_techs.append({"id": tactic[0], "name": tactic[1]})

m_tactics = retrieve_unique_techniques()
m_tactics_formated = [f"{tactic['id']}:{tactic['name']}" for tactic in m_tactics]

name_list = []

for tactic in attack_techs:
    print(tactic['id'])
    # retrive all id from m_tactics list of objects
    print(m_tactics)
    if tactic['id'] in [tactic['id'] for tactic in m_tactics]:
        # Find the matching tactic by id
        matching_tactic = next((m_tactic for m_tactic in m_tactics if m_tactic['id'] == tactic['id']), None)
        if matching_tactic:
            name_list.append({'name': tactic['name'], 'matching_name': matching_tactic['name']})

print(f"Number of techniques: {(attack_techs)}")
print(f"number of matches: {sum([tac['name'] == tac['matching_name'] for tac in name_list])}")

print("techniques length:", len(tactic_dist_data["techniques"]))

print(tactic_dist_data["techniques"].keys())

#%% Plotting cumulative attack of unique techniqes vs sessions
plt.figure(figsize=(12, 6))
plt.plot(unique_techniques_data["session_cum_num_techniques"], marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Cumulative sum of unique techniques")
plt.xlabel("Session")
plt.ylabel("Number of Unique techniques")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

plt.ylim(bottom=0)
# plt.grid()
plt.legend()
plt.show()

# %%

print(unique_techniques_data)

plt.figure(figsize=(12, 6))
plt.plot(unique_techniques_data["session_num_techniques"][0:30],
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

tactics = list(tactic_dist_data["tactics"].keys())
techniques = list(tactic_dist_data["tactics"].keys())

print(tactic_dist_data["tactics_heatmap"])

plt.figure(figsize=(15, 20))
plt.imshow(tactic_dist_data["tactics_heatmap"])
plt.xlabel("Session")
plt.ylabel("Tactic")
plt.yticks(range(len(tactics)), tactics)

# %%

tactics = list(tactic_dist_data["techniques"].keys())
techniques = list(tactic_dist_data["techniques"].keys())

print(tactic_dist_data["techniques_heatmap"])

plt.figure(figsize=(15, 20))
plt.imshow(tactic_dist_data["techniques_heatmap"])
plt.xlabel("Session")
plt.ylabel("Technique")
plt.yticks(range(len(tactics)), tactics)

# %%

import matplotlib.pyplot as plt

# your data
tactics = list(tactic_dist_data["tactics"].keys())
values  = list(tactic_dist_data["tactics"].values())

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


# %%
import matplotlib.pyplot as plt
import numpy as np

tactics_list = list(sorted(tactic_dist_data["session_tactics"],
    key=lambda data: sum(list(data.values())), reverse=True))[:5]

for i, tactics in enumerate(tactics_list):
    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    labels = list(tactics.keys())
    stats  = list(tactics.values())
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    stats += stats[:1]
    angles += angles[:1]
    
    ax.plot(angles, stats, '-', linewidth=2, c=colors.scheme[i], alpha=0.5, label=f"Session number {i}: length = {sum(tactics.values())}")
    ax.fill(angles, stats, alpha=0.2, c=colors.scheme[i])
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    plt.figlegend()
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

plt.figure(figsize=(12, 6))
plt.plot(entropy_techniques_data["entropies"], marker="o", linestyle="-", c=colors.scheme[0])
plt.title("Experiment entropy of unique techniques")
plt.xlabel("Session")
plt.ylabel("Entropy of unique techniques")

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
plt.title("Config entropy")
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
