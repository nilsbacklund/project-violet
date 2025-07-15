import numpy as np
from typing import Dict, List, Any
from Purple.Data_analysis.metrics import measure_tactic_distribution

def compute_entropy(probs: np.ndarray) -> float:
    log_probs = np.nan_to_num(np.log(probs), neginf=0)
    return (-probs * log_probs).sum()

def measure_entropy_techniques(sessions: List[Dict]) -> Dict[str, Any]:
    techniques_data = measure_tactic_distribution(sessions)
    techniques_dict: Dict[str, int] = techniques_data["techniques"]
    session_techniques_data: List[Dict[str, int]] = techniques_data["session_techniques"]
    print(techniques_dict)
    print(session_techniques_data)
    print()
    
    unique_techniques = list(techniques_dict.keys())
    counts = np.array(list(techniques_dict.values()))
    session_counts = np.zeros((len(session_techniques_data)+1, len(counts)))
    session_counts[-1,:] = counts
    technique_to_index = { technique:i for i, technique in enumerate(unique_techniques)}

    for i, session in enumerate(session_techniques_data):
        if session:
            for technique, count in session.items():
                index = technique_to_index[technique]
                counts[index] -= count
        session_counts[len(session_techniques_data)-1-i,:] = counts
    
    session_probs = session_counts[1:,:] / session_counts[1:,:].sum(axis=1, keepdims=True)
    log_probs = np.nan_to_num(np.log(session_probs), neginf=0)
    session_entropies = np.sum(-session_probs * log_probs, axis=1)
    
    results = {
        "entropies": session_entropies,
        "unique_techniques": unique_techniques,
        "counts": session_counts[1:],
        "probabilities": session_probs
    }
    return results

def measure_entropy_session_length(sessions: List[Dict]) -> Dict[str, Any]:
    session_lengths = [session.get("length", 0) for session in sessions]
    session_lengths = np.array(session_lengths)
    unique_lengths, counts = np.unique(session_lengths, return_counts=True)
    session_counts = np.zeros((len(session_lengths)+1, len(counts)))
    session_counts[-1,:] = counts
    length_to_index = { length:i for i, length in enumerate(unique_lengths) }

    for i, length in enumerate(session_lengths):
        index = length_to_index[length]
        counts[index] -= 1
        session_counts[len(session_lengths)-1-i,:] = counts

    session_probs = session_counts[1:,:] / session_counts[1:,:].sum(axis=1, keepdims=True)
    log_probs = np.nan_to_num(np.log(session_probs), neginf=0)
    session_entropies = np.sum(-session_probs * log_probs, axis=1)
    
    results = {
        "entropies": session_entropies,
        "unique_lengths": unique_lengths,
        "counts": session_counts[1:],
        "probabilities": session_probs
    }

    return results