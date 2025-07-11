from pathlib import Path
import os
import sys
import questionary

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Red.extraction import extract_session
from Utils.jsun import load_json, append_json_to_file

BASE_DIR = Path(__file__).resolve().parent.parent

def safe_listdir(p: Path):
    """Return listdir if p exists and is a dir, else empty list."""
    return os.listdir(p) if p.exists() and p.is_dir() else []

if __name__ == "__main__":
    logs_path = BASE_DIR / "logs"
    all_experiments = sorted(
        [name for name in safe_listdir(logs_path) if name.startswith("experiment")]
    )

    if not all_experiments:
        print("No experiments found under", logs_path)
        sys.exit(1)

    # multi‑select checkbox prompt
    selected = questionary.checkbox(
        "Select experiments to extract:",
        choices=all_experiments
    ).ask()

    if not selected:
        print("Nothing selected, exiting.")
        sys.exit(0)

    for experiment in selected:
        experiment_path = logs_path / experiment
        print(f"\n>> Processing: {experiment}")

        for config in sorted(filter(lambda name: name.startswith("hp_config"), safe_listdir(experiment_path))):
            config_path = experiment_path / config
            full_logs_path = config_path / "full_logs"
            session_path = config_path / "sessions.json"

            # remove existing sessions.json
            if session_path.exists():
                session_path.unlink()
                print(f"  • Removed existing: {session_path.name}")

            attack_files = safe_listdir(full_logs_path)
            sorted_attacks = sorted(
                attack_files,
                key=lambda fn: int(Path(fn).stem.split('_')[-1])
            )

            for attack in sorted_attacks:
                attack_path = full_logs_path / attack
                logs = load_json(attack_path)
                session = extract_session(logs)
                append_json_to_file(session, session_path, False)
                print(f"    √ Extracted {attack}")