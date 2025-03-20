import heapq
from annoy import AnnoyIndex
from fastapi import logger
import numpy as np
from src.logger_config import setup_logger
from gigachat import GigaChat

logger = setup_logger(__name__)

# GigaChat credentials
GIGACHAT_CREDENTIALS = "YWQxMDllYmQtZDA0ZC00MDM2LWEyMjktMWU1ZTJlOTViNzkyOmY2NWU0YjE2LWE0ZDctNGNlOC05M2RiLWZkZjgwZDc5YTUyYw=="

def rrf_rank(indexes1, scores1, indexes2, scores2, k=60):
    rank_dict = {}
    
    # Add scores from first list
    for idx, score in zip(indexes1, scores1):
        rank_dict[idx] = rank_dict.get(idx, 0) + 1/(k + (1 - score))  # Convert score to rank-like value
        
    # Add scores from second list
    for idx, score in zip(indexes2, scores2):
        rank_dict[idx] = rank_dict.get(idx, 0) + 1/(k + (1 - score))  # Convert score to rank-like value
        
    # Sort by RRF score (descending) and return both indices and scores
    sorted_items = sorted(rank_dict.items(), 
                         key=lambda x: -x[1])  # Sort by score (descending)
    
    # Unpack into separate lists
    sorted_indices = [item[0] for item in sorted_items]
    sorted_scores = [item[1] for item in sorted_items]
    
    return sorted_indices, sorted_scores

def simple_rank(name_indices, customer_name_indices):
    # Create a dictionary to store scores
    score_dict = {}
    
    # Score items from name query
    for idx in name_indices:
        score_dict[idx] = score_dict.get(idx, 0) + 1
        
    # Score items from customer_name query
    for idx in customer_name_indices:
        score_dict[idx] = score_dict.get(idx, 0) + 1
        
    # Sort by score (descending) and then by index (ascending)
    sorted_indices = sorted(score_dict.keys(), 
                          key=lambda x: (-score_dict[x], x))
    
    return sorted_indices, [score_dict[idx] for idx in sorted_indices]


def search_faster(query, tenders, key, top_k, model):
    # Получаем вектор запроса с помощью GigaChat
    with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
        embedding_response = giga.embeddings([query]).data[0]
        query_vector = np.array(embedding_response.embedding)
    print(query_vector.shape)
    print(tenders[0][key].shape)
    
    similarities = []
    valid_indices = []

    # Calculate similarities directly
    for i, tender in enumerate(tenders):
        if tender[key] is not None:
            tender_vector = tender[key]
            # Calculate cosine similarity
            cos_sim = np.dot(query_vector, tender_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(tender_vector)
            )
            similarities.append(cos_sim)
            valid_indices.append(i)

    # Get top_k results using heapq for better performance
    top_results = heapq.nlargest(
        top_k, 
        zip(similarities, valid_indices), 
        key=lambda x: x[0]
    )

    # Unpack results
    if top_results:
        sorted_similarities, sorted_indices = zip(*top_results)
        return list(sorted_indices), list(sorted_similarities)
    
    return [], []

def search(query, tenders, key, top_k, model):
    query_vector = model.get_embeddings([query])[0]
    
    # Create Annoy index dynamically
    annoy_index = AnnoyIndex(model.embedding_dim, 'angular')
        
    # Generate embeddings for filtered tenders
    valid_tenders_count = 0
    for i, tender in enumerate(tenders):
        # Use pre-computed vector if available, otherwise compute
        if tender[key] is not None:
            tender_vector = tender[key]
            
            # Add to Annoy index
            annoy_index.add_item(i, tender_vector)
            valid_tenders_count += 1

    # Build the index
    annoy_index.build(10)  # 10 trees for index construction
    
    # Find nearest neighbors
    nearest_indices, distances = annoy_index.get_nns_by_vector(
        query_vector, 
        top_k, 
        include_distances=True
    )
    
    # Convert angular distances to similarities using the utility function
    similarities = [angular_distance_to_similarity(distance) for distance in distances]
    
    return nearest_indices, similarities


def angular_distance_to_similarity(distance: float) -> float:
    """
    Convert angular distance to similarity score.
    For angular distance, similarity = cos(θ) = 1 - distance
    Normalizes to range [0, 1]
    """
    similarity = 1 - (distance / 2)  # Convert angular distance to cosine similarity
    return max(0.0, min(1.0, similarity))  # Ensure score is between 0 and 1
