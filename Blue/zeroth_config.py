import textgrad as tg
from dotenv import load_dotenv
import os
from pathlib import Path
import sys
import json

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Blue.utils import clean_and_finalize_config, extract_json
from Blue.new_config_pipeline import save_config_as_file

env = load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

MAX_TOKENS = 3000

from textgrad import logger
class TextualGradientDescentWithKwargs(tg.TGD):
    def step(self, **kwargs):
        """
        Perform a single optimization step.
        This method updates the parameters of the optimizer by generating new text using the engine and updating the parameter values accordingly.
        It also logs the optimizer response and the updated text.
        Returns:
            None
        """
        for parameter in self.parameters:
            prompt_update_parameter = self._update_prompt(parameter)
            new_text = self.engine(prompt_update_parameter, system_prompt=self.optimizer_system_prompt, **kwargs)
            logger.info(f"TextualGradientDescent optimizer response", extra={"optimizer.response": new_text})
            try:
                new_value = new_text.split(self.new_variable_tags[0])[1].split(self.new_variable_tags[1])[0].strip()
            # Check if we got a cannot be indexed error
            except IndexError:
                logger.error(f"TextualGradientDescent optimizer response could not be indexed", extra={"optimizer.response": new_text})
                raise IndexError(f"TextualGradientDescent optimizer response could not be indexed. This can happen if the optimizer model cannot follow the instructions. You can try using a stronger model, or somehow reducing the context of the optimization. Response: {new_text}")
            parameter.set_value(new_value)
            logger.info(f"TextualGradientDescent updated text", extra={"parameter.value": parameter.value})
            if self.verbose:
                print("-----------------------TextualGradientDescent------------------------")
                print(parameter.value)
            
            if self.do_gradient_memory:
                self.update_gradient_memory(parameter)

# gpt-4o mini is ass with textgrad, use gpt-4.1-mini
engine = tg.get_engine("gpt-4.1-mini")

tg.set_backward_engine(engine, override=True)

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
        "Only point out, as concisely as possible, where it violates any of the requirements below (always mention what the requirements are):\n\n"
        "1. At least 2 of each service type (HTTP, SSH, TCP)\n"
        "2. Atleast half of each service type need to be LLM‐powered\n"
        "3. Well‐defined vulnerabilities for attackers\n"
        "(Do not suggest or MENTION to add commands to TCP services. The TCP service should have no commands. Do not mention this!).\n\n"
        f"Configuration schema that must be followed: {schema_text}\n"
    )

    loss_fn = tg.TextLoss(critique_prompt)
    
    optimizer = TextualGradientDescentWithKwargs(parameters=[new_config])

    # Run optimization
    for step in range(5):
        loss = loss_fn(new_config)
        print(f"Step {step+1} loss:", loss)
        # Make the config update conform to the JSON schema
        loss.value += f"\nThis configuration schema must be followed: {schema_text}"
        loss.backward()
        optimizer.step(max_tokens=MAX_TOKENS)
        print(f"Updated config:\n{new_config.value}\n")
        print("-" * 50)

    json_str = extract_json(new_config.value)
    config = json.loads(json_str)
    clean_config = clean_and_finalize_config(config)

    print(json.dumps(clean_config, indent=4))
    save_config_as_file(clean_config)

    # add validation

if __name__ == "__main__":
    main()