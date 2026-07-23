import numpy as np
from typing import List, Dict, Set

def precision_at_k(actual: List[str], predicted: List[str], k: int) -> float:
    if not actual or not predicted:
        return 0.0
    predicted_k = predicted[:k]
    score = 0
    for item in predicted_k:
        if item in actual:
            score += 1
    return score / k

def recall_at_k(actual: List[str], predicted: List[str], k: int) -> float:
    if not actual or not predicted:
        return 0.0
    predicted_k = predicted[:k]
    score = 0
    for item in predicted_k:
        if item in actual:
            score += 1
    return score / len(actual)

def ndcg_at_k(actual: List[str], predicted: List[str], k: int) -> float:
    if not actual or not predicted:
        return 0.0
    predicted_k = predicted[:k]
    dcg = 0.0
    for i, item in enumerate(predicted_k):
        if item in actual:
            dcg += 1.0 / np.log2(i + 2)
            
    idcg = 0.0
    # ideal dcg is if all actual items were positioned at the top of predicted list
    for i in range(min(k, len(actual))):
        idcg += 1.0 / np.log2(i + 2)
        
    if idcg == 0.0:
        return 0.0
    return dcg / idcg

def calculate_coverage(all_recs: List[List[str]], catalog: Set[str]) -> float:
    if not catalog:
        return 0.0
    unique_recommended = set()
    for rec_list in all_recs:
        unique_recommended.update(rec_list)
    return len(unique_recommended.intersection(catalog)) / len(catalog)

def calculate_diversity(all_recs: List[List[str]], item_features: Dict[str, Set[str]]) -> float:
    """
    Intra-list diversity metric using Jaccard distance between item genres/features.
    """
    diversities = []
    for rec_list in all_recs:
        if len(rec_list) <= 1:
            continue
        distances = []
        for i in range(len(rec_list)):
            for j in range(i+1, len(rec_list)):
                item_a = rec_list[i]
                item_b = rec_list[j]
                
                feat_a = item_features.get(item_a, set())
                feat_b = item_features.get(item_b, set())
                
                union = feat_a.union(feat_b)
                if not union:
                    dist = 1.0
                else:
                    intersect = feat_a.intersection(feat_b)
                    dist = 1.0 - (len(intersect) / len(union))
                distances.append(dist)
        if distances:
            diversities.append(np.mean(distances))
    return float(np.mean(diversities)) if diversities else 1.0
