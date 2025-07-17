import numpy as np
from typing import Dict, List, Any, Literal
from Purple.Data_analysis.metrics import measure_mitre_distribution

def compute_entropy(probs: np.ndarray) -> float:
    log_probs = np.nan_to_num(np.log(probs), neginf=0)
    return (-probs * log_probs).sum()

def measure_entropy_mitre(sessions: List[Dict[str, Any]],
        variable: Literal["tactics", "techniques"]) -> Dict[str, Any]:
    mitre_data = measure_mitre_distribution(sessions)
    mitre_dict: Dict[str, int] = mitre_data[variable]
    session_mitre_data: List[Dict[str, int]] = mitre_data[f"session_{variable}"]
    
    unique_t = list(mitre_dict.keys())
    counts = np.array(list(mitre_dict.values()))
    session_counts = np.zeros((len(session_mitre_data)+1, len(counts)))
    session_counts[-1,:] = counts
    t_to_index = { t:i for i, t in enumerate(unique_t)}

    for i, session in enumerate(session_mitre_data):
        if session:
            for t, count in session.items():
                index = t_to_index[t]
                counts[index] -= count
        session_counts[len(session_mitre_data)-1-i,:] = counts
    
    session_probs = session_counts[1:,:] / session_counts[1:,:].sum(axis=1, keepdims=True)
    log_probs = np.nan_to_num(np.log(session_probs), neginf=0)
    session_entropies = np.sum(-session_probs * log_probs, axis=1)
    
    results = {
        "entropies": session_entropies,
        "unique": unique_t,
        "counts": session_counts[1:],
        "probabilities": session_probs
    }
    return results

def measure_entropy_tactics(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return measure_entropy_mitre(sessions, "tactics")

def measure_entropy_techniques(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return measure_entropy_mitre(sessions, "techniques")

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