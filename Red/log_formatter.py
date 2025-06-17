# %%
def format_logs_for_network(full_logs, session_id):
    formated_logs = []
    for i, attack_log in enumerate(full_logs):
        for j, log in enumerate(attack_log):
            # Ensure the log is a dictionary
            if isinstance(log, dict):
                log_dict = log
            else:
                log_dict = log.__dict__

            # Add session_id to each log entry
            log_dict['session_id'] = session_id

            # Update the log in the attack_log
            attack_log[j] = log_dict

    return formated_logs

# %% test
# get full logs from logs/full_logs_test_id.json
def test_format_logs_for_network():
    import json

    with open('../logs/full_logs_test_id.json', 'r') as f:
        full_logs = json.load(f)

    formatted_logs = format_logs_for_network(full_logs, 'test_id')
    print(formatted_logs)


test_format_logs_for_network()

# %%
