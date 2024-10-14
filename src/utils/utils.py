import logging
import csv
import json
import os
from typing import List, Dict
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = os.path.join(Path("logs"), f"oklink_data_fetcher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # files
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def save_to_csv(data: List[Dict], chain: str, date: datetime, block_number: int):
    if not data:
        return

    # path: chain\year\month\day\block_number
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    csv_dir = os.path.join(Path("data"), chain, "csv", year, month, day, str(block_number))

    file_path = os.path.join(csv_dir, "transactions.csv")
    os.makedirs(csv_dir, exist_ok=True)
    
    file_exists = os.path.exists(file_path)
    keys = data[0].keys()

    with open(file_path, 'a', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        if not file_exists:
            dict_writer.writeheader()
        dict_writer.writerows(data)

def save_to_json(data: Dict, chain: str, date: datetime, block_number: int, page: int):
    date_str = date.strftime("%Y_%m_%d")
    json_dir = os.path.join(Path("data"), chain, "json", date_str)
    os.makedirs(json_dir, exist_ok=True)
    file_path = os.path.join(json_dir, f"block_{block_number}_page_{page}.json")

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)