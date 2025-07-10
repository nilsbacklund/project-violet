# extract json from a file
import json
from pathlib import Path
from typing import List, Dict, Any
from Utils.jsun import load_json
from collections import Counter

current_path = Path(__file__)
base_path = current_path.parent
path = base_path / "logs/logs/hp_config_1/sessions.json"

data = load_json(Path(path))
command_session_lengths: List[int] = []
