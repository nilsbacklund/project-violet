import numpy as np

def kl_divergence(p0: np.ndarray, p: np.ndarray):
    """
        p0: old distribution
        p: new distribution
    """
    elements = p0 * np.log(p0 / p)
    return np.nan_to_num(elements).sum()

if __name__ == "__main__":
    p0 = np.array([0.1, 0.4, 0.2, 0.2, 0])
    p = np.array([0.1, 0.4, 0.2, 0.2, 0])
    print(kl_divergence(p0, p))