#!/usr/bin/env python3
"""
Скрипт для предварительной загрузки моделей перед запуском приложения
"""
import os
import argparse
from transformers import AutoTokenizer, AutoModel
from src.logger_config import setup_logger

logger = setup_logger("model_download")

def download_model(model_name, output_dir):
    """
    Загружает модель и токенизатор и сохраняет их локально
    """
    logger.info(f"Загрузка модели {model_name} в директорию {output_dir}")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Загрузка и сохранение токенизатора
        logger.info("Загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=output_dir)
        
        # Загрузка и сохранение модели
        logger.info("Загрузка модели...")
        model = AutoModel.from_pretrained(model_name, cache_dir=output_dir)
        
        logger.info(f"Модель {model_name} успешно загружена")
        return True
    except Exception as e:
        logger.error(f"Ошибка при загрузке модели: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Загрузка языковых моделей")
    parser.add_argument("--model", type=str, default="ai-forever/ruRoberta-large", 
                        help="Название модели для загрузки")
    parser.add_argument("--output", type=str, default="resources/models", 
                        help="Директория для сохранения модели")
    
    args = parser.parse_args()
    download_model(args.model, args.output) 