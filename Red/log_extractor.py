import subprocess
import datetime
import json
import os

last_checked = datetime.datetime.now(datetime.UTC).isoformat()
def get_new_hp_logs():
    """
    Fetch new logs from the Beelzebub container since the last check.
    Returns a list of parsed JSON objects or raw logs if parsing fails.
    """
    global last_checked
    process = subprocess.Popen(
        ["sudo", "docker", "logs", f"{os.getenv("RUNID")}_blue_lagoon_1", "--since", last_checked],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    last_checked = datetime.datetime.now(datetime.UTC).isoformat()

    log_output = process.stdout.read().strip()
    if log_output:
        #print(log_output)
        try:
            log_lines = log_output.strip().split('\n')
            logs = [json.loads(line) for line in log_lines if line.strip()]
            return logs  # Return parsed JSON objects instead of string
        except json.JSONDecodeError:
            # If parsing fails, return raw logs as fallback
            return {"raw_logs": log_output, "error": "Failed to parse JSON"}

        # trace = langfuse.trace(name="on-demand-log-check")
        # for line in log_output.splitlines():
        #     trace.span(name="log").log(line)

    return []  # Return empty list instead of empty string
