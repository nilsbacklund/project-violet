#%%

import os
import ipywidgets as widgets
from IPython.display import display

experiment_names = [name for name in os.listdir("../logs")[::-1] if str(name).startswith("experiment")]

dropdown = widgets.Dropdown(
    options=experiment_names,
    description="Pick an experiment to analyze:",
)

display(dropdown)

#%%

selected_experiment = dropdown.value
from pathlib import Path
from Utils.jsun import load_json
import pprint
from Data_analysis.metrics import measure_session_length, measure_tactic_distribution, measure_unique_techniques

path = Path("..") / "logs" / selected_experiment
configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]
for config in configs:
    sessions = load_json(path / config / "sessions.json")
    pprint.pprint(sessions)
    pprint.pprint(measure_session_length(sessions))
    pprint.pprint(measure_tactic_distribution(sessions))
    pprint.pprint(measure_unique_techniques(sessions))

#%%

