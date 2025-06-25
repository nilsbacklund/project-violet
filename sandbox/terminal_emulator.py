from pathlib import Path
import sys, os, json
import questionary
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Console, Group
from rich.box import ROUNDED

console = Console()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parent.parent
experiments_path = BASE_DIR / "logs" / "full_logs"

if __name__ == "__main__":
    experiment_choice = questionary.select(
        "Pick an experiment folder:",
        choices=os.listdir(experiments_path)
    ).ask()

    configs_path = experiments_path / experiment_choice
    config_choice = questionary.select(
        "Pick a configuration folder:",
        choices=os.listdir(configs_path)
    ).ask()

    attacks_path = configs_path / config_choice
    attack_choice = questionary.select(
        "Pick an attack JSON file:",
        choices=os.listdir(attacks_path)
    ).ask()
    
    file_path = attacks_path / attack_choice
    with open(file_path, "r", encoding="utf8") as f:
        attack_logs = json.load(f)[0]
    
    for iteration in attack_logs:
        # Collect individual panels
        panels = []

        i = iteration["iteration"]
        message = iteration["llm_response"]["message"]
        function_type = iteration["llm_response"]["function"]
        arguments = iteration["llm_response"]["arguments"]
        response = str(iteration.get("tool_response", "")) or "<no output>"

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