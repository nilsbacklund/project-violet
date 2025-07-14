#%%

import os
import sys
from pathlib import Path
# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ipywidgets as widgets
from IPython.display import display

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
import pprint
import numpy as np
from Data_analysis.metrics import measure_session_length, measure_tactic_distribution, measure_unique_techniques

path = logs_path / selected_experiment
configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]

sessions_list = [load_json(path / config / "sessions.json") for config in configs]

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


#%% Plotting cumulative attack of unique techniqes vs sessions
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(unique_techniques_data["session_cum_num_techniques"], marker="o", linestyle="--")
plt.title("Cumulative sum of unique techniques")
plt.xlabel("Session")
plt.ylabel("Number of Unique Tactics")
plt.ylim(bottom=0)
plt.grid()
plt.legend()
plt.show()

# %%

plt.figure(figsize=(12, 6))
plt.plot(unique_techniques_data["session_num_techniques"], marker="o", linestyle="--")
plt.title("Number of Unique Tactics per Session")
plt.xlabel("Session")
plt.ylabel("Number of Unique Tactics")
plt.grid()
plt.ylim(bottom=0)
plt.legend()
plt.show()

# %% Session length

plt.figure(figsize=(12, 6))
plt.plot(length_data["session_lengths"], marker="o", linestyle="--")
plt.title("Session length per Session")
plt.xlabel("Session")
plt.ylabel("Session length")

for index in reconfig_indices:
    plt.axvline(index - 0.5, color="k", linestyle="--")

plt.grid()
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
plt.plot(prompt_tokens, marker="o", linestyle="--")
# plt.plot(cached_tokens, marker="o", linestyle="--")
plt.plot(completion_tokens, marker="o", linestyle="--")
plt.title("Tokens per Session")
plt.xlabel("Session")
plt.ylabel("Session length")

for index in token_reconfig_indices:
    plt.axvline(index - 0.5, color="k", linestyle="--")

plt.grid()
plt.ylim(bottom=0)
plt.legend()
plt.show()

# %%
