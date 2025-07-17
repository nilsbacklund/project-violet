#!/usr/bin/env python3
import subprocess
import sys
import questionary
from pathlib import Path
import os
import tarfile

# Run this code to download logs

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    # SSH in and list the directory
    result = subprocess.run(
        ['ssh', "attack@honey-attack", 'ls', "project-violet/logs"],
        capture_output=True,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    sys.stderr.write(f"ERROR: could not list logs: {e}\n")
    sys.exit(1)

all_experiments = sorted(result.stdout.split("\n"), reverse=True)

selected_experiments = questionary.checkbox(
    "Select experiments to download:",
    choices=all_experiments
).ask()

if not selected_experiments:
    print("Nothing selected, exiting.")
    sys.exit(0)

save_attacks = questionary.confirm(
    "Do you you want to save attack files as well? (this requires way more storage)"
).ask()

for experiment in selected_experiments:
    print(f"Downloading {experiment}")
    experiment_path = BASE_DIR / "logs" / experiment
    os.makedirs(experiment_path, exist_ok=True)

    # Build tar command, excluding attack files only if save_attacks is False
    exclude_flag = "--exclude='attack*'" if not save_attacks else ""
    remote_tar_cmd = (
        f"tar cz {exclude_flag} -C project-violet/logs/{experiment} ."
    )

    # Run remote tar and capture to local .tar.gz
    tar_file_name = f"{experiment}.tar.gz"
    local_tar_path = experiment_path / tar_file_name
    with open(local_tar_path, 'wb') as tar_out:
        subprocess.run(
            ['ssh', 'attack@honey-attack', remote_tar_cmd],
            stdout=tar_out,
            shell=False,
            check=True
        )

    # Extract the tarball locally and remove it
    with tarfile.open(local_tar_path, 'r:gz') as tar:
        tar.extractall(path=experiment_path)
    os.unlink(local_tar_path)