import os
import json
from typing import List, Optional
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
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
import traceback
import re 
import sqlite3

logger = setup_logger(__name__)
model = 0  # ModelFactory.get_model(ModelType.roberta)

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

class SearchRequest(BaseModel):
    query: str
    region: str = None
    top_k: int = 10

class Database:
    def __init__(self):
        self.db_path = "resources/tenders.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def get_tenders(self, region: str, start_date: str, end_date: str, limit: int = 1000):
        query = """
        SELECT 
            id,
            name,
            price,
            law_type,
            purchase_method,
            okpd2_code,
            publish_date,
            end_date,
            results_date,
            customer_inn,
            customer_name,
            region,
            date_added
        FROM tenders 
        WHERE region = ? 
        AND date_added BETWEEN ? AND ?
        ORDER BY date_added DESC
        LIMIT ?
        """
        
        self.cursor.execute(query, (region, start_date, end_date, limit))
        rows = self.cursor.fetchall()
        
        return [dict(row) for row in rows]

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

def get_traceback(e: Exception) -> str:
    """Получить полную трассировку ошибки в виде строки"""
    return ''.join(traceback.format_exception(type(e), e, e.__traceback__))

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
        error_traceback = get_traceback(ve)
        logger.error(f"Ошибка валидации даты: {str(ve)}\nПолный traceback:\n{error_traceback}")
        raise HTTPException(status_code=400, detail={
            "error": f"Invalid date format: {str(ve)}",
            "traceback": error_traceback
        })
    except Exception as e:
        error_traceback = get_traceback(e)
        logger.error(f"Ошибка загрузки тендеров: {str(e)}\nПолный traceback:\n{error_traceback}")
        raise HTTPException(status_code=500, detail={
            "error": f"Error downloading tenders: {str(e)}",
            "traceback": error_traceback
        })

@app.post("/search-tenders/")
async def search_tenders(request: SearchRequest):
    """
    Эндпоинт для поиска тендеров
    
    Args:
        request: Тело запроса с параметрами поиска
        
    Returns:
        list: Список найденных тендеров
    """
    # TENDER ID
    for ch in request.query.strip():
        if not ch.isdigit():
            tender_id = None
            break
        else:
            tender_id = request.query
            tenders = db.get_tenders(tender_id=tender_id.strip())
            if len(tenders) > 0:
                tender = tenders[0]
                return [{
                    'id': tender['id'],
                    'name': tender['name'],
                    'price': float(tender['price']) if tender['price'] else 0,
                    'law_type': tender.get('law_type'),
                    'purchase_method': tender.get('purchase_method'),
                    'okpd2_code': tender.get('okpd2_code'),
                    'publish_date': tender.get('publish_date'),
                    'end_date': tender.get('end_date'),
                    'customer_inn': tender.get('customer_inn'),
                    'customer_name': tender.get('customer_name'),
                    'region': tender.get('region'),
                    'similarity_score': 1
                }]
            else:
                return [{
                    'id': 'no-results',
                    'name': 'Тендеры не найдены',
                    'price': 0,
                    'law_type': '',
                    'purchase_method': '',
                    'okpd2_code': '',
                    'publish_date': '',
                    'end_date': '',
                    'customer_inn': '',
                    'customer_name': '',
                    'region': '',
                    'similarity_score': 0,
                    'no_results': True  # Специальное поле для определения отсутствия результатов
                }]
    

               
    # Анализируем запрос с помощью GigaChat, передаем регион если он указан
    parsed_data = parse_query(request.query, region_code=request.region)
    
    # Логируем распарсенные данные
    logger.info(f"Parsed query: {parsed_data}")
    
    # Убедимся, что в parsed_data есть все необходимые ключи
    if not isinstance(parsed_data, dict):
        parsed_data = {"query": request.query}
    if "query" not in parsed_data or not parsed_data["query"]:
        parsed_data["query"] = request.query
    if "заказчик" not in parsed_data:
        parsed_data["заказчик"] = None

    # Фильтруем тендеры по параметрам из запроса
    tenders = db.get_tenders(
        region=parsed_data.get("region"),
        date=parsed_data.get("date"),
        min_price=parsed_data.get("min_price"),
        max_price=parsed_data.get("max_price"),
        law_type=parsed_data.get("document"),
        purchase_method=parsed_data.get("type"),
        okpd2_code=parsed_data.get("окпд2"),
        customer_inn=parsed_data.get("инн"),
        keywords=parsed_data.get("keywords")
    )

    if not tenders:
        logger.warning("Не найдено тендеров после фильтрации")
        # Возвращаем специальный объект вместо пустого массива
        return [{
            'id': 'no-results',
            'name': 'Тендеры не найдены',
            'price': 0,
            'law_type': '',
            'purchase_method': '',
            'okpd2_code': '',
            'publish_date': '',
            'end_date': '',
            'customer_inn': '',
            'customer_name': '',
            'region': '',
            'similarity_score': 0,
            'no_results': True  # Специальное поле для определения отсутствия результатов
        }]
        
    logger.info(f"Найдено тендеров после фильтрации: {len(tenders)}")
        
    # Выполняем поиск по названию
    nearest_indices_by_name = search_faster(
        parsed_data['query'], 
        tenders, 
        'vectors_gigachat', 
        request.top_k, 
        model
    )
    
    # Если указан заказчик, ищем и по заказчику
    if parsed_data['заказчик'] is not None:
        logger.info(f"Поиск по заказчику: {parsed_data['заказчик']}")
        nearest_indices_by_customer_name = search_faster(
            parsed_data['заказчик'], 
            tenders, 
            'vector_customer_name', 
            len(tenders) // 2, 
            model
        )
        
        # Выполняем ранжирование по RRF
        nearest_indices = rrf_rank(
            nearest_indices_by_name[0], 
            nearest_indices_by_name[1], 
            nearest_indices_by_customer_name[0], 
            nearest_indices_by_customer_name[1], 
            k=60
        )
    else:
        nearest_indices = nearest_indices_by_name

    # Подготавливаем результаты поиска
    results = []
    i = 0
    for idx, similarity_score in zip(nearest_indices[0], nearest_indices[1]):
        if idx >= len(tenders):
            continue
            
        tender = tenders[idx]
        
        try:
            results.append({
                'id': tender['id'],
                'name': tender['name'],
                'price': float(tender['price']) if tender['price'] else 0,
                'law_type': tender.get('law_type'),
                'purchase_method': tender.get('purchase_method'),
                'okpd2_code': tender.get('okpd2_code'),
                'publish_date': tender.get('publish_date'),
                'end_date': tender.get('end_date'),
                'customer_inn': tender.get('customer_inn'),
                'customer_name': tender.get('customer_name'),
                'region': tender.get('region'),
                'similarity_score': float(similarity_score)
            })
            i += 1
            if i == request.top_k:
                break
        except Exception as e:
            logger.error(f"Ошибка создания результата для тендера {tender.get('id', 'unknown')}: {str(e)}")
            continue
    
    logger.info(f"Возвращаем {len(results)} похожих тендеров")
    
    return results

if __name__ == "__main__":
    uvicorn.run(
        "src.tenders_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        limit_request_line=0,  # No limit
        limit_request_fields=0,  # No limit
        limit_request_field_size=0  # No limit
    )