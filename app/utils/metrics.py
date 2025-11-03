def precision_at_k(recommended_ids, relevant_ids, k):
    recommended_k = recommended_ids[:k]
    hits = len(set(recommended_k) & set(relevant_ids))
    return hits / k

def recall_at_k(recommended_ids, relevant_ids, k):
    recommended_k = recommended_ids[:k]
    hits = len(set(recommended_k) & set(relevant_ids))
    return hits / len(relevant_ids) if relevant_ids else 0

def evaluate_topk_metrics(recommendations, ground_truth_ids, k_list=[1, 3, 5]):
    rec_ids = [rec['bookId'] for rec in recommendations]
    results = {}
    for k in k_list:
        results[f"Precision@{k}"] = precision_at_k(rec_ids, ground_truth_ids, k)
        results[f"Recall@{k}"] = recall_at_k(rec_ids, ground_truth_ids, k)
    return results