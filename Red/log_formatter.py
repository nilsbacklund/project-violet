# %%
from Red.model import DataLogObject, LabledCommandObject

def format_logs_to_lables(full_logs, session_id):
    """
        Format the full logs to a list of LabledCommandObject instances.
        Each command is associated with its MITRE ATT&CK tactic and technique.
    """
    
    formated_logs = []
    for i, attack_log in enumerate(full_logs):
        formated_log_attack = []
        for j, log in enumerate(attack_log):
            if isinstance(log, dict):
                log_dict = log
            else:
                log_dict = log.__dict__

            if not log_dict['llm_response']:
                continue

            if not log_dict['llm_response'].__dict__['function'] == 'terminal_input':
                continue

            tactic = log_dict['mitre_attack_method'].__dict__['tactic_used']
            technique = log_dict['mitre_attack_method'].__dict__['technique_used']

            if not tactic or not technique:
                continue

            if not log_dict['beelzebub_response']:
                continue

            for resp in log_dict['beelzebub_response']:
                if not resp['command']:
                    continue

                command = resp['command']
                
                formated_log = LabledCommandObject(
                    command=command,
                    tactic=tactic,
                    technique=technique
                )

                formated_log_attack.append(formated_log)

        if formated_log_attack:
            formated_logs.append({
                'session_id': session_id,
                'logs': formated_log_attack
            })

    return formated_logs

# %% test
# get full logs from logs/full_logs_test_id.json
def test_format_logs_to_lables():
    import json

    with open('../logs/full_logs_test_id.json', 'r') as f:
        full_logs = json.load(f)

    formatted_logs = format_logs_to_lables(full_logs, 'test_id')
    print(formatted_logs)


def save_labels(formatted_logs, session_id):
    import os
    import json

    if not os.path.exists('logs/labels'):
        os.makedirs('logs/labels')

    with open(f'logs/labels/labels_{session_id}.json', 'w') as f:
        json.dump([log.to_dict() for log in formatted_logs], f, indent=4)

    print(f"Labels saved to logs/labels/labels_{session_id}.json")

# test_format_logs_to_lables()

# %%
