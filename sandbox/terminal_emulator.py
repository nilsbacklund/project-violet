from pathlib import Path
import sys, os, json
import questionary
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Console
from rich.rule import Rule
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
        console.print(Rule())  # visual separator

        message       = iteration["llm_response"]["message"]
        function_type = iteration["llm_response"]["function"]
        arguments     = iteration["llm_response"]["arguments"]
        response      = str(iteration["tool_response"])

        if message:
            console.print(
                Panel(message, title="Attacker thoughts", border_style="green", box=ROUNDED)
            )

        match function_type:
            case "run_command":
                cmd = arguments["command"]
                tactic = arguments["tactic_used"]
                technique = arguments["technique_used"]
                # Build two panels
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

                # Print them side by side
                console.print(Columns([panel_cmd, panel_meta], expand=True, equal=True))

                if response.startswith(cmd):
                    response = response[len(cmd):].strip()
                console.print(
                    Panel(response or "[dim]<no output>[/dim]",
                          title="Tool response output", border_style="blue", box=ROUNDED)
                )
            case None:
                pass
            case _:
                raise Exception("Unknown function type!")

        # ←— pause here until Enter is pressed
        console.print("[dim]Press [bold]Enter[/bold] to continue…[/dim]", end="")
        input()