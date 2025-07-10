# This file will extract all logs
# OVERWRITES ALREADY CREATED SESSIONS

from pathlib import Path
import os
import questionary
import sys

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Preprocessing.extraction import extract_session
from Utils.jsun import load_json, append_json_to_file

BASE_DIR = Path(__file__).resolve().parent.parent

def safe_listdir(p: Path):
    """Return listdir if p exists and is a dir, else empty list."""
    return os.listdir(p) if p.exists() and p.is_dir() else []

if __name__ == "__main__":
    logs_path = BASE_DIR / "logs"

    for experiment in sorted(filter(lambda name: name.startswith("experiment"), safe_listdir(logs_path))):
        experiment_path = logs_path / experiment

        extract = questionary.confirm(
            f"Do you want to extract '{experiment}'?"
        ).ask()

        if not extract:
            print(f"Skipped: {experiment}")
            continue

        for config in filter(lambda name: name.startswith("hp_config"), safe_listdir(experiment_path)):
            config_path = experiment_path / config
            full_logs_path = config_path / "full_logs"
            session_path = config_path / "sessions.json"

            # remove sessions if exist
            if session_path.exists():
                session_path.unlink()
                print(f"Removed existing: {session_path}")

            attack_files = safe_listdir(full_logs_path)
            sorted_attacks = sorted(
                attack_files,
                key=lambda name: int(Path(name).stem.split('_')[-1])
)
            for attack in attack_files:
                attack_path = full_logs_path / attack
                attack_number = attack.split("_")[-1]
                logs = load_json(attack_path)

                session = extract_session(logs)

                append_json_to_file(session, session_path, False)
                print(f"Extracted attack: {attack_path}")