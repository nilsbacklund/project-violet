import json
from jsonschema import validate, ValidationError
from pathlib import Path

try:
    with open("beelzebub_config.json", "r") as f:
        config = json.load(f)

    with open("data/services_schema.json", "r") as s:
        schema = json.load(s)

    # Validate the whole config object
    validate(instance=config, schema=schema)
    print("\nBeezlebub honeypot Config is valid according to the schema.")

except ValidationError as ve:
    print(f"\n Validation failed: {ve.message}")
    print(f"At path: {'/'.join(map(str, ve.path))}")
except Exception as e:
    print(f"\n Error: {e}")
