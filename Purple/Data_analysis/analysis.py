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
filter_empty_sessions = True
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

# pprint.pprint(combined_sessions)
# pprint.pprint(len(combined_sessions))
# pprint.pprint(measure_session_length(combined_sessions))
# pprint.pprint(measure_tactic_distribution(combined_sessions))
# pprint.pprint(measure_unique_techniques(combined_sessions))

#%%

