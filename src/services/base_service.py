import ssl
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
        self._MAX_TRIES = 7
        self._ALERT_THRESHOLD = 5
        self._RETRY_DELAY = 3
        self._rate_limiter = MultiKeyRateLimiter(api_keys, 5)  # 5 requests per second per key

    async def _make_request(self, url: str, params: Dict):
        for attempt in range(self._MAX_TRIES):
            try:
                if attempt >= self._ALERT_THRESHOLD:
                    self._logger.error(f"Attempt {attempt + 1} of {self._MAX_TRIES} for {url}")
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
            except (httpx.HTTPStatusError, ssl.SSLError, httpx.ReadTimeout) as e:
                self._logger.warning(f"Error occurred: {e}. Attempt {attempt + 1} of {self._MAX_TRIES}")
                if attempt == self._MAX_TRIES - 1:
                    raise
            except Exception as e:
                self._logger.error(f"Unexpected error occurred: {e}")
                if attempt == self._MAX_TRIES - 1:
                    raise
            
            self._logger.debug(f"Retrying in {self._RETRY_DELAY} seconds")
            await asyncio.sleep(self._RETRY_DELAY)
    
        raise Exception(f"Failed to make request after {self._MAX_TRIES} attempts")

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

    async def get_transactions_for_single_block(self, block_number: int, date: datetime = datetime.now().date()) -> List[Dict]:
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
            
            # save_to_json(data, self.CHAIN_NAME, date, block_number, page)

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
    
    async def get_block_height_by_time(self, target_time: datetime, closest: str = "before") -> int:
        url = "https://www.oklink.com/api/v5/explorer/block/block-height-by-time"
        params = {
            "chainShortName": self.CHAIN_NAME,
            "time": int(target_time.timestamp() * 1000),
            "closest": closest
        }
        response = await self._make_request(url, params)
        return int(response["data"][0]["height"])
    
    async def get_block_time(self, block_number: int) -> datetime:
        url = "https://www.oklink.com/api/v5/explorer/block/block-fills"
        params = {
            "chainShortName": self.CHAIN_NAME,
            "height": block_number
        }
        response = await self._make_request(url, params)
        block_time_str = response["data"][0]["blockTime"]
        block_time_ms = int(block_time_str)
        
        return datetime.fromtimestamp(block_time_ms / 1000)