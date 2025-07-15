import math
from collections import Counter

def entropy(prob_dist, base=math.e):
    return -sum(p * math.log(p, base) for p in prob_dist if p > 0)

def get_prob_dist(data):
    total = sum(data.values())
    return [freq / total for freq in data.values()]

if __name__ == "__main__":
    data = ['cat', 'dog', 'cat', 'bird', 'cat', 'dog']
    data = Counter(data)
    print(data)
    print(get_prob_dist(data))
    print(entropy(get_prob_dist(data)))
    print(entropy(get_prob_dist(data), base=2))