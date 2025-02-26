import os
import json
from typing import List, Optional
from datetime import datetime
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from annoy import AnnoyIndex
from src.chat_gpt import parse_query
from src.download_tenders import (
    download_tenders,
    OUTPUT_DIR,
)
from src.logger_config import setup_logger
from src.models import ModelFactory, ModelType, BaseEmbeddingModel
import numpy as np
from src.database import Database
from src.search_utils import search, angular_distance_to_similarity, rrf_rank, search_faster, simple_rank

logger = setup_logger(__name__)
model = ModelFactory.get_model(ModelType.roberta)

# Ensure resources directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
db = Database()
app = FastAPI(
    title="Tenders Search API",
    description="API for downloading and searching tenders from zakupki.gov.ru",
    version="1.0.0"
)

class TenderDownloadRequest(BaseModel):
    regions: Optional[List[str]] = Field(
        default=["77", "78"],
        description="List of region codes to download tenders from"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for tender search (YYYY-MM-DD)",
        example="2024-10-01"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for tender search (YYYY-MM-DD)",
        example="2024-10-02"
    )
    vectorize: Optional[bool] = Field(
        default=True,
        description="Create vector embeddings for downloaded tenders"
    )
    model_type: Optional[ModelType] = Field(
        default=ModelType.roberta,
        description="Model to use for vectorization: 'roberta' or 'fasttext'"
    )

class TenderSearchRequest(BaseModel):
    query: str = Field(
        description="Text query to search for similar tenders"
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of similar tenders to return"
    )

class TenderSearchResult(BaseModel):
    id: int
    name: str
    price: float
    law_type: Optional[str]
    purchase_method: Optional[str]
    okpd2_code: Optional[str]
    publish_date: Optional[str]
    end_date: Optional[str]
    customer_inn: Optional[str]
    customer_name: Optional[str]
    region: Optional[str]
    similarity_score: float


def create_tender_embeddings(tenders_summary_path: str, model: BaseEmbeddingModel):
    """Create embeddings for tenders using the specified model."""
    try:
        with open(tenders_summary_path, 'r', encoding='utf-8') as f:
            tenders = json.load(f)

        tender_texts = list(tenders.values())
        tender_keys = list(tenders.keys())

        logger.info(f"Building embeddings using {model.__class__.__name__}...")
        embeddings = model.get_embeddings(tender_texts)

        if embeddings is None:
            raise ValueError("Failed to generate embeddings")

        # Create and save index
        annoy_index = AnnoyIndex(model.embedding_dim, 'angular')
        tenders_metadata = {}

        for i, (embedding, key, text) in enumerate(zip(embeddings, tender_keys, tender_texts)):
            annoy_index.add_item(i, embedding)
            tenders_metadata[i] = {
                'purchase_number': key,
                'tender_name': text
            }

        annoy_index.build(10)
        model_name = model.__class__.__name__.lower().replace('model', '')
        annoy_index.save(f'{OUTPUT_DIR}/tenders_index_{model_name}.ann')

        with open(f'{OUTPUT_DIR}/tenders_metadata_{model_name}.json', 'w', encoding='utf-8') as f:
            json.dump(tenders_metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Created ANNOY index with {len(tenders_metadata)} tenders")
        return True
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        return False

@app.post("/download-tenders/")
async def api_download_tenders(request: TenderDownloadRequest):
    try:
        if request.start_date:
            datetime.strptime(request.start_date, '%Y-%m-%d')
        if request.end_date:
            datetime.strptime(request.end_date, '%Y-%m-%d')

        # Download tenders
        download_tenders(
            regions=request.regions,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Create embeddings if requested
        if request.vectorize:
            success = create_tender_embeddings(request.model_type)
            if not success:
                raise Exception("Failed to create embeddings")

        # Return results
        db = Database()
        tenders_summary = db.get_all_tenders()
        
        return {
            "message": "Tenders downloaded successfully",
            "total_tenders": len(tenders_summary),
            "summary": tenders_summary,
            "model_type": request.model_type
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading tenders: {str(e)}")


@app.post("/search-tenders/",
          response_model=List[TenderSearchResult])
async def api_search_tenders(request: TenderSearchRequest):
    # Log the incoming search request
    logger.info(f"Received search request: query='{request.query}', top_k={request.top_k}")
    
    # Parse the query 
    parsed_query = parse_query(request.query)
    logger.info(f"Parsed query={parsed_query}")
    
    # Log parsed query parameters
    logger.debug(f"Parsed query parameters: {parsed_query}")
    
    # Filter tenders based on parsed query parameters
    tenders = db.get_tenders(
        region=parsed_query.get("region"),
        date=parsed_query.get("date"),
        min_price=parsed_query.get("min_price"),
        max_price=parsed_query.get("max_price"),
        law_type=parsed_query.get("document"),
        purchase_method=parsed_query.get("type"),
        okpd2_code=parsed_query.get("окпд2"),
        customer_inn=parsed_query.get("инн"),
    )
    
    print(tenders[0]['vector_customer_name'].shape)
    
    # Log number of filtered tenders
    logger.info(f"Number of filtered tenders: {len(tenders)}")
    
    logger.info(f"Start search by name: {parsed_query['query']}")
    nearest_indices_by_name = search_faster(parsed_query['query'], tenders, 'vector', request.top_k, model)
    
    if parsed_query['заказчик'] is not None:
        logger.info(f"Start search by customer: {parsed_query['заказчик']}")
        nearest_indices_by_customer_name = search_faster(parsed_query['заказчик'], tenders, 'vector_customer_name', len(tenders) // 2, model)
    
        # RRF rank
        nearest_indices = rrf_rank(nearest_indices_by_name[0], 
                                   nearest_indices_by_name[1], 
                                   nearest_indices_by_customer_name[0], 
                                   nearest_indices_by_customer_name[1], 
                                   k=60)
        #nearest_indices = simple_rank(nearest_indices_by_name[0], 
        #                              nearest_indices_by_customer_name[0])
    else:
        nearest_indices = nearest_indices_by_name
    

    # Prepare search results
    search_results = []
    i = 0
    for idx, similarity_score in zip(nearest_indices[0], nearest_indices[1]):
        tender = tenders[idx]
        #similarity_score = distance # angular_distance_to_similarity(distance)
        
        search_results.append(TenderSearchResult(
            id=tender['id'],
            name=tender['name'],
            price=tender['price'],
            law_type=tender['law_type'],
            purchase_method=tender['purchase_method'],
            okpd2_code=tender['okpd2_code'],
            publish_date=tender['publish_date'],
            end_date=tender['end_date'],
            customer_inn=tender['customer_inn'],
            customer_name=tender['customer_name'],
            region=tender['region'],
            similarity_score=similarity_score
        ))
        i += 1
        if i == request.top_k:
            break
    
    # Log search results
    logger.info(f"Returning {len(search_results)} similar tenders")
    
    return search_results

if __name__ == "__main__":
    uvicorn.run(
        "tenders_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )