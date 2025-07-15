# %%
mock_data = [5, 2, 5, 6, 3, 4, 5, 9, 2, 8, 9, 10]

import json
from enum import Enum
from typing import List, Dict, Any
from pathlib import Path
from Red.model import ReconfigMethod

def reconfig_criteria_met(all_techniques_list: List[set], method) -> bool:
    if method == ReconfigMethod.NO_RECONFIG:
        return False
    elif method == ReconfigMethod.NEW_TECHNIQUES:
        if len(all_techniques_list) < 2:
            return False
        if all_techniques_list[-1] < all_techniques_list[-2]:
            return True
        return False
    elif method == ReconfigMethod.SESSION_LENGTH:
        print("")
    return False


def new_techniques_reconfigure(all_techniques_list: List[set]) -> bool:
    if len(all_techniques_list) < 2:
        return False
    if len(all_techniques_list[-1]) < len(all_techniques_list[-2]):
        return True
    return False

def new_techniques_smooth(all_techniques_list: List[set]) -> bool:
    len_list = [len(techniques) for techniques in all_techniques_list]
    if len(all_techniques_list) < 2:
        return False
    if len(all_techniques_list[-1]) == len(all_techniques_list[-2]):
        return True
    return False

if __name__ == "__main__":
    print(reconfig_criteria_met(mock_data, ReconfigMethod.NEW_TECHNIQUES))
# %%
