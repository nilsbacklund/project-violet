import textgrad as tg
from dotenv import load_dotenv
import os
from pathlib import Path

env = load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# gpt-4o mini is ass with textgrad, use gpt-4.1-mini
tg.set_backward_engine("gpt-4.1-mini")

BASE_DIR = Path(__file__).resolve().parent

schema_path = BASE_DIR.parent / 'Blue' / 'RagData' / 'services_schema.json'

def main():
    new_config = tg.Variable('config_json: { "services": [] }',
        requires_grad=True,
        role_description="The new Beelzebub honeypot configuration to optimize")
    
    with open(schema_path, "r", encoding="utf8") as f:
        schema_text = f.read()

    critique_prompt = (
        "You are a security‐expert reviewer.  "
        "I will show you a honeypot configuration in JSON; **do not** re‐emit or re‐write the config.  "
        "Only point out, as concisely as possible, where it violates any of the requirements below:\n\n"
        "- At least 5 distinct services (HTTP, SSH, TCP)\n"
        "- Atleast half of the services need to be LLM‐powered\n"
        "- Well‐defined vulnerabilities for attackers\n\n"
        f"Schema: {schema_text}\n\n"
    )

    loss_fn = tg.TextLoss(critique_prompt)
    
    optimizer = tg.TGD(parameters=[new_config])

    # Run optimization
    for step in range(5):
        loss = loss_fn(new_config)
        print(f"Step {step+1} loss:", loss)
        # Make the config update conform to the JSON schema
        loss.value += f"\nThis configuration schema must be followed: {schema_text}"
        loss.backward()
        optimizer.step()
        print(f"Updated config:\n{new_config.value}\n")
        print("-" * 50)
    

if __name__ == "__main__":
    main()