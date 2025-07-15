# %%
mock_data = [5, 2, 5, 6, 3, 4, 5, 9, 2, 8, 9, 10]
set1 = set([1, 4, 3, 6, 2])
set2 = set([6, 1, 8, 6, 10])
set3 = set([1, 5, 3, 10, 2])
mock_data = [set1, set2, set3]

import json
from enum import Enum
from typing import List, Dict, Any
from pathlib import Path
from Red.model import ReconfigMethod
import numpy as np

def reconfig_criteria_met(all_techniques_list: List[set], method) -> bool:
    if method == ReconfigMethod.NO_RECONFIG:
        return new_techniques_reconfigure(all_techniques_list, 20, 0.06)
    elif method == ReconfigMethod.NEW_TECHNIQUES:
        return new_techniques_reconfigure(all_techniques_list, 3, 0.5)
    elif method == ReconfigMethod.SESSION_LENGTH:
        print("")
    return False


def new_techniques_reconfigure_old_not_working_as_it_should(all_techniques_list: List[set]) -> bool:
    if len(all_techniques_list) < 2:
        return False
    print(all_techniques_list)
    if len(all_techniques_list[-1]) < len(all_techniques_list[-2]):
        return True
    return False

def new_techniques_reconfigure(all_techniques_list: List[set], n_avg=5, limit=0.5) -> bool:
    unique_techniques = set()
    n_new_techniques_list = []

    for tech in all_techniques_list:
        new_tech = tech - unique_techniques
        unique_techniques.update(tech)
        n_new_techniques_list.append(len(new_tech))

    n_new_techniques_list = np.array(n_new_techniques_list)
    last_avg = limit+1
    print(n_new_techniques_list)

    if len(n_new_techniques_list) < n_avg:
        last_avg = np.mean(n_new_techniques_list)
        print(last_avg, limit)
    else:
        last_avg = np.mean(n_new_techniques_list[-n_avg:])
        print(last_avg, limit)

    return last_avg < limit

if __name__ == "__main__":
    print(reconfig_criteria_met(mock_data, ReconfigMethod.NEW_TECHNIQUES))
# %%
