# project-violet

## Overview

Project Violet is an automated cybersecurity research platform that simulates realistic attack scenarios against configurable honeypots to generate labeled datasets for improving defensive capabilities. The system uses AI-powered red team attacks, adaptive blue team defenses, and the Beelzebub honeypot to create a continuous feedback loop for cybersecurity improvement.

## Running the code easy

The easiest way to run the code is through the main entry point:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main simulation loop
python main.py
```

The [main.py](main.py) file orchestrates the entire attack simulation cycle, running multiple configurations and collecting comprehensive attack data.

## Configuration

### Main Configuration (`config.py`):

```python
# LLM Models
llm_model_sangria = LLMModel.GPT_4O_MINI  # Red team model
llm_model_config = LLMModel.GPT_4_1_NANO   # Blue team model

# Simulation Settings
simulate_command_line = True    # Use simulated vs real attacks
save_logs = True               # Enable comprehensive logging
save_configuration = True      # Only saves new configuration when True
attacks_per_configuration = 10 # Attacks per honeypot config
n_configurations = 10         # Total configurations to test
```

### Environment Setup:

```bash
# Required environment variables
export OPENAI_API_KEY="your-openai-api-key"
```

## Output Structure

The system generates organized output in the `logs/` directory:

```
logs/
├── full_logs_[session_id].json      # Complete attack logs
└── formatted/                       # Processed attack data
BeelzebubServices
└── config_[session_id].json         # Used honeypot configs
```

## Directory Structure

```
project-violet/
├── main.py
├── config.py
├── Red/
├── Blue/
├── Purple/
├── Blue_Lagoon/
├── BeelzebubServices/
├── temp/
├── logs/
```

## Structure of code

The codebase is organized into three main components:

### 🔴 Red Team (Attack Simulation)

* **Sangria**: AI-powered attack orchestration system
* **Tool Integration**: Automated execution of attack commands

### 🔵 Blue Team (Defense & Reconfiguration)

* **Configuration Pipeline**: Dynamic honeypot reconfiguration based on previous configurations and attack patterns
* **RAG System**: Using a RAG to retrieve vulnerabilities from NVD

### 🍯 Honeypot (Beelzebub)

* **Service Simulation**: Realistic vulnerable service emulation
* **Interaction Logging**: Comprehensive attack interaction capture
* **Configuration**: Iterative service modification capabilities

## Red Team and Sangria

The Red Team component (`Red/`) implements an AI-driven attack simulation framework:

### Key Components:

* **`sangria.py`**: Main attack orchestration engine

  * Manages attack sessions and iterations
  * Coordinates between LLM models and target systems

* **`model.py`**: Data structures and LLM model definitions

  * Defines attack data logging objects
  * Manages different LLM model configurations

* **`tools.py`**: Attack tool implementations

  * Selects the correct tools from the model output
  * Defines action for all tool (run\_command, search\_web, terminate)

* **`defender_llm.py`**: LLM integration for defender responses

  * Either a LLM acting like a Kali Linux terminal
  * Or connected to a real Kali Linux terminal

* **`log_formatter.py`**: Attack data processing

  * Start of preprocessing data
  * Formats raw attack logs for analysis

* `ssh_utils.py`: Establishes SSH sessions to run commands remotely on a real or emulated Kali Linux system.

* `sangria_config.py`: Stores global simulation parameters such as timeout, retry count, and verbosity for each Sangria session.

* `schema.py`: Defines the structure of prompts, responses, and LLM-interaction messages to ensure consistency across different LLM backends and attacker tools.

### Attack Flow:

1. Generate attack strategies using LLM models
2. Execute commands against honeypot targets
3. Log interactions and responses
4. Apply MITRE ATT\&CK framework categorization

## Blue Team and Reconfiguration

The Blue Team component (`Blue/`) handles generation of new honeypot configurations:

### Key Components:

* **`new_config_pipeline.py`**: Honeypot reconfiguration engine

  * Analyzes attack patterns from previous configurations and logs
  * RAG retrieval of vulnerabilities
  * Generates new honeypot configurations

* **`embedder.py`**: Vector embedding for pattern matching

  * Creates semantic representations of vulnerability
  * Enables similarity-based pattern detection

* **`services.py`**: Service configuration management

  * Manages honeypot service schemas

* **`validate_config.py`**: Validates honeypot config files against a predefined JSON schema.

* **`utils.py`**: Provides helper functions for loading files, logging, and processing.

* **`BAAI_bge.py`**: Loads the BAAI/bge model for generating vector embeddings.

* **`RagData/vulns_embeddings_bge_m3.npy`**: Precomputed embeddings of vulnerabilities using BAAI-bge-m3.

* **`RagData/services_schema.json`** : JSON schema used to validate the structure of service configs.

### Defensive Adaptation Process:

1. Collect attack data from honeypot interactions
2. Analyze attack patterns and previous configs
3. Retrieve vulnerability to exploit and not yet explored
4. Generate improved honeypot configurations
5. Deploy new configurations to counter detected attack patterns

## Blue Lagoon - Honeypot Orchestration Layer

The `Blue_Lagoon/` module converts honeypot configurations into fully deployable containerized services. It orchestrates the launching of Cowrie (for baseline deception) and Beelzebub (for AI-powered traps) using Docker Compose.

### Running Beelzebub

```bash
# Launch Beelzebub honeypot
docker-compose -f docker-compose-beelzebub.yml up --build
```

### Key Files:

* `docker-compose-beelzebub.yml`: Spins up Beelzebub honeypot containers using generated service files.
* `main.go`: Golang-based engine for parsing service configs and generating deployment instructions.
* `builder/builder.go`: Converts JSON/YAML configurations into runtime services.
* `parser/parser.go`: Parses and validates honeypot configurations.
* `honeypot_tools.py`: Optional Python utility for validating service configuration structure before deployment.

## Honeypot Beelzebub

"Beelzebub is an advanced honeypot framework designed to provide a highly secure environment for detecting and analyzing cyber attacks. It offers a low code approach for easy implementation and uses AI to mimic the behavior of a high-interaction honeypot." [Link](https://github.com/mariocandela/beelzebub)

### BeelzebubServices/

This folder stores finalized honeypot configuration files generated by the Blue configuration engine. Each file defines a service's port, protocol, vulnerability theme, and interactive behavior. These configurations are consumed directly by the Beelzebub honeypot and simulate various network services.

## temp/

This folder stores draft honeypot configuration files before validation or deployment. It supports experimentation and quick iteration during development.

## Research Applications

This platform supports various cybersecurity research objectives:

* **Attack Pattern Discovery**: Identify novel attack techniques
* **Defense Effectiveness**: Measure defensive countermeasure success
* **Honeypot Optimization**: Improve honeypot detection capabilities
* **Threat Intelligence**: Generate realistic attack datasets
* **AI Security Research**: Study AI-powered attack and defense systems
