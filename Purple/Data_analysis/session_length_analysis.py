# %%

# extract json from a file
import json
from pathlib import Path
from typing import List, Dict, Any
from Utils.jsun import load_json
from collections import Counter

current_path = Path(__file__)
base_path = current_path.parent.parent.parent
path = base_path / "logs/experiment_2025-07-10T22_03_01/hp_config_1/sessions.json"

data = load_json(Path(path))
command_session_lengths: List[int] = []

for session in data:
    command_session_length = session.get("length", 0)
    command_session_lengths.append(command_session_length)

# Variance of session lengths
mean_length = sum(command_session_lengths) / len(command_session_lengths)
variance = sum((x - mean_length) ** 2 for x in command_session_lengths) / len(command_session_lengths)
std_dev = variance ** 0.5
print(f"Mean session length: {mean_length}")
print(f"Variance of session lengths: {variance}")
print(f"Standard deviation: {std_dev}")

# Min, max, and range
min_length = min(command_session_lengths)
max_length = max(command_session_lengths)
range_length = max_length - min_length
print(f"Min session length: {min_length}")
print(f"Max session length: {max_length}")
print(f"Range: {range_length}")

# Median and quartiles
sorted_lengths = sorted(command_session_lengths)
n = len(sorted_lengths)
median = sorted_lengths[n//2] if n % 2 == 1 else (sorted_lengths[n//2-1] + sorted_lengths[n//2]) / 2
q1 = sorted_lengths[n//4]
q3 = sorted_lengths[3*n//4]
print(f"Median: {median}")
print(f"Q1: {q1}, Q3: {q3}")
print(f"Interquartile Range (IQR): {q3 - q1}")

# Session length distribution
length_counts = Counter(command_session_lengths)
print(f"Most common session lengths: {length_counts.most_common(5)}")

# Percentage of short vs long sessions
short_sessions = sum(1 for length in command_session_lengths if length < mean_length)
long_sessions = len(command_session_lengths) - short_sessions
print(f"Sessions below average: {short_sessions} ({short_sessions/len(command_session_lengths)*100:.1f}%)")
print(f"Sessions above average: {long_sessions} ({long_sessions/len(command_session_lengths)*100:.1f}%)")

# Outlier detection (using IQR method)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
outliers = [length for length in command_session_lengths if length < lower_bound or length > upper_bound]
print(f"Outliers: {outliers}")
print(f"Number of outliers: {len(outliers)} ({len(outliers)/len(command_session_lengths)*100:.1f}%)")



# %%
