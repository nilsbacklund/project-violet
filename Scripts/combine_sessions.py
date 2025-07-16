from pathlib import Path
import os
import sys
import questionary

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.jsun import load_json, save_json_to_file

BASE_DIR = Path(__file__).resolve().parent.parent

def safe_listdir(p: Path):
    """Return listdir if p exists and is a dir, else empty list."""
    return os.listdir(p) if p.exists() and p.is_dir() else []

if __name__ == "__main__":
    logs_path = BASE_DIR / "logs"
    all_experiments = sorted(
        safe_listdir(logs_path),
        reverse=True
    )

    if not all_experiments:
        print("No experiments found under", logs_path)
        sys.exit(1)

    extract_omni = questionary.confirm(
        "Do you only want to combine omni sessions as well?",
        default=False
    ).ask()

    # multi‑select checkbox prompt
    selected = questionary.checkbox(
        "Select experiments to combine sessions in:",
        choices=all_experiments
    ).ask()

    if not selected:
        print("Nothing selected, exiting.")
        sys.exit(0)

    for experiment in selected:
        experiment_path = logs_path / experiment
        print(f"\n>> Processing: {experiment}")

        configs = filter(lambda name: name.startswith("hp_config"), safe_listdir(experiment_path))
        sorted_configs = sorted(
            configs,
            key=lambda fn: int(Path(fn).stem.split('_')[-1])
        )

        sessions_list = [load_json(experiment_path / config / "sessions.json") for config in sorted_configs]
        combined_sessions = sum(sessions_list, [])
        save_json_to_file(combined_sessions, experiment_path / "sessions.json")

        if extract_omni:
            omni_sessions_list = [load_json(experiment_path / config / "omni_sessions.json") for config in sorted_configs]
            combined_omni_sessions = sum(omni_sessions_list, [])
            save_json_to_file(combined_omni_sessions, experiment_path / "omni_sessions.json")
        print(f"Combined {len(combined_sessions)} sessions in {experiment}")