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
print(selected_experiment)
from Utils.jsun import load_json
import pprint
from Data_analysis.metrics import measure_session_length, measure_tactic_distribution, measure_unique_techniques

path = logs_path / selected_experiment
configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]
for config in configs:
    sessions = load_json(path / config / "sessions.json")
    pprint.pprint(sessions)
    pprint.pprint(measure_session_length(sessions))
    pprint.pprint(measure_tactic_distribution(sessions))
    pprint.pprint(measure_unique_techniques(sessions))

#%%

