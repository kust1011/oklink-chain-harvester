import httpx
import logging
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.rate_limiter import MultiKeyRateLimiter
from src.utils.utils import save_to_csv, save_to_json
from typing import Iterator, List, Dict
import time

class BaseService:
    def __init__(self, api_keys: List[str], logger: logging.Logger):
        self._logger = logger
        self._MAX_TRIES = 5
        self._RETRY_DELAY = 3
        self._rate_limiter = MultiKeyRateLimiter(api_keys, 5)  # 5 requests per second per key

    async def _make_request(self, url: str, params: Dict):
        for attempt in range(self._MAX_TRIES):
            try:
                self._logger.debug(f"Attempting to acquire API key, attempt {attempt + 1}")
                api_key = await self._rate_limiter.acquire()
                self._logger.debug(f"Acquired API key: {api_key[:5]}...")
                headers = {'Ok-Access-Key': api_key}
                async with httpx.AsyncClient(timeout=10) as client:
                    self._logger.debug(f"Sending request to {url}")
                    response = await client.get(url=url, headers=headers, params=params)
                    response.raise_for_status()
                    self._logger.debug("Request successful")
                    return response.json()
            except httpx.HTTPStatusError as e:
                self._logger.warning(f"HTTP error occurred: {e}. Attempt {attempt + 1} of {self._MAX_TRIES}")
                if attempt == self._MAX_TRIES - 1:
                    raise
            except Exception as e:
                self._logger.error(f"An error occurred: {e}")
                raise
            
            self._logger.debug(f"Retrying in {self._RETRY_DELAY} seconds")
            await asyncio.sleep(self._RETRY_DELAY)

    async def get_latest_block_number(self) -> int:
        url = "https://www.oklink.com/api/v5/explorer/block/block-height-by-time"
        current_time = int(time.time() * 1000)  # milliseconds
        params = {
            "chainShortName": self.CHAIN_NAME,
            "time": str(current_time),
            "closest": "before"
        }

        data = await self._make_request(url, params)
        return int(data["data"][0]["height"])

    async def get_transactions_for_single_block(self, block_number: int, date: datetime) -> List[Dict]:
        url = "https://www.oklink.com/api/v5/explorer/block/transaction-list"
        params = {
            "chainShortName": self.CHAIN_NAME,
            "height": block_number,
            "protocolType": "transaction",
            "limit": 100,
            "page": 1
        }

        all_transactions = []
        page = 1

        while True:
            data = await self._make_request(url, params)
            
            save_to_json(data, self.CHAIN_NAME, date, block_number, page)

            if "data" in data and data["data"]:
                block_data = data["data"][0]
                transactions = block_data.get("blockList", [])
                all_transactions.extend(transactions)
                
                total_pages = int(block_data.get("totalPage", 1))
                if page >= total_pages:
                    break
                
                page += 1
                params["page"] = page
            else:
                break

        return all_transactions

    async def get_latest_transactions(self, num_blocks: int = 10) -> List[Dict]:
        latest_block = await self.get_latest_block_number()
        all_transactions = []
        current_date = datetime.now()

        for i in range(num_blocks):
            block_number = latest_block - i
            transactions = await self.get_transactions_for_single_block(block_number, current_date)
            for tx in transactions:
                tx['blockNumber'] = block_number
            all_transactions.extend(transactions)

        return all_transactions

    async def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        self._logger.info(f"Fetching transactions from {start_date.date()} to {end_date.date()}")
        all_transactions = []

        while start_date <= end_date:
            next_date = min(start_date + timedelta(days=1), end_date)
            start_block = await self.get_block_height_by_time(start_date)
            end_block = await self.get_block_height_by_time(next_date)
            
            self._logger.info(f"Fetching blocks from {start_block} to {end_block} for {start_date.date()}")
            
            for block_number in range(start_block, end_block + 1):
                transactions = await self.get_transactions_for_single_block(block_number, start_date)
                all_transactions.extend(transactions)
                self._logger.info(f"Fetched {len(transactions)} transactions for block {block_number}")
            
            start_date = next_date + timedelta(microseconds=1)

        return all_transactions
    
    async def get_block_height_by_time(self, target_time: datetime, closest: str = "before") -> int:
        url = "https://www.oklink.com/api/v5/explorer/block/block-height-by-time"
        params = {
            "chainShortName": self.CHAIN_NAME,
            "time": int(target_time.timestamp() * 1000),
            "closest": closest
        }
        response = await self._make_request(url, params)
        return int(response["data"][0]["height"])

    def _save_json(self, data: Dict, filename: str):
        json_dir = Path("data/json")
        json_dir.mkdir(parents=True, exist_ok=True)
        with open(json_dir / f"{filename}.json", "w") as f:
            json.dump(data, f, indent=2)