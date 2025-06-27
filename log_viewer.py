from pathlib import Path
import sys, os, json
import questionary
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Console, Group
from rich.box import ROUNDED

console = Console()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parent
experiments_path = BASE_DIR / "logs"

if __name__ == "__main__":
    experiments = list(sorted(filter(lambda name: name.startswith("experiment"), os.listdir(experiments_path)), reverse=True))
    experiment_choice = questionary.select(
        "Pick an experiment folder:",
        choices=experiments
    ).ask()

    configs_path = experiments_path / experiment_choice
    configs = list(sorted(filter(lambda name: name.startswith("hp_config"), os.listdir(configs_path)),
        key=lambda config_file: int(config_file.split("_")[-1])))
    config_choice = questionary.select(
        "Pick a configuration folder:",
        choices=configs
    ).ask()

    attacks_path = configs_path / config_choice / "full_logs"
    attacks = list(sorted(os.listdir(attacks_path), key=lambda attack_file: int(attack_file.split("_")[-1][:-5])))
    attack_choice = questionary.select(
        "Pick an attack JSON file:",
        choices=attacks
    ).ask()
    
    file_path = attacks_path / attack_choice
    with open(file_path, "r", encoding="utf8") as f:
        attack_logs = json.load(f)
    
    for iteration in attack_logs:
        # Collect individual panels
        panels = []

        i = iteration["iteration"]
        message = iteration["llm_response"]["message"]
        function_type = iteration["llm_response"]["function"]
        arguments = iteration["llm_response"]["arguments"]
        response = iteration["tool_response"]
        bz_response = iteration["beelzebub_response"]

        if bz_response:
            raise Exception("beelzebub response returned")
        
        # Attacker Thoughts
        if message:
            panels.append(
                Panel(
                    message,
                    title="Attacker thoughts",
                    border_style="green",
                    box=ROUNDED,
                    expand=True
                )
            )

        # Function-specific panels
        if function_type == "run_command":
            cmd = arguments["command"]
            tactic = arguments["tactic_used"]
            technique = arguments["technique_used"]
            panel_cmd = Panel(
                f"$ {cmd}",
                title="Run Command",
                border_style="red",
                box=ROUNDED,
                expand=True
            )
            panel_meta = Panel(
                f"[bold]Tactic[/bold]: {tactic}\n[bold]Technique[/bold]: {technique}",
                title="MITRE ATT&CK",
                border_style="yellow",
                box=ROUNDED,
                expand=True
            )
            # add side-by-side
            panels.append(Columns([panel_cmd, panel_meta], expand=True, equal=True))

            if response.startswith(cmd):
                response = response[len(cmd):].strip()

        elif function_type == "web_search_tool":
            query = arguments["query"]
            panels.append(
                Panel(
                    query,
                    title="Web search query",
                    border_style="magenta",
                    box=ROUNDED,
                    expand=True
                )
            )

        # Tool response
        if response:
            panels.append(
                Panel(
                    response,
                    title="Tool response output",
                    border_style="blue",
                    box=ROUNDED,
                    expand=True
                )
            )

        # Wrap all panels into a parent panel
        group = Group(*panels)
        console.print(
            Panel(
                group,
                title=f"Iteration {i}",
                border_style="white",
                box=ROUNDED,
                expand=True
            )
        )

        console.print("[dim]Press [bold]Enter[/bold] to continue…[/dim]", end="")
        input()