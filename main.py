import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from src.factory import ServiceFactory
from src.utils.utils import save_to_csv, setup_logger
from asyncio import Semaphore

# Fetch transactions for a given number of blocks
async def fetch_transactions(service, blocks_to_fetch: int) -> List[Dict]:
    return await service.get_latest_transactions(blocks_to_fetch)

# Filter and format transaction data
def filter_transactions(transactions: List[Dict]) -> List[Dict]:
    return [
        {
            'hash': tx.get('txid', ''),
            # 'block_hash': tx.get('blockHash', ''),
            'block_number': tx.get('height', ''),
            'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # 'from_address': tx.get('from', ''),
            # 'to_address': tx.get('to', ''),
            # 'value': tx.get('amount', ''),
            # 'gas': tx.get('txfee', ''),
            # 'block_timestamp': tx.get('transactionTime', ''),
        }
        for tx in transactions
    ]

async def process_chain_by_block_number(chain: str, block_number: int, logger: logging.Logger):
    try:
        service = ServiceFactory.get_service(chain)
        transactions = await service.get_transactions_for_single_block(block_number)
        filtered_transactions = filter_transactions(transactions)

        block_time = await service.get_block_time(block_number)
        
        save_to_csv(filtered_transactions, chain, block_time.date(), block_number)
        logger.info(f"Saved {len(filtered_transactions)} transactions for block {block_number}")
    except Exception as e:
        logger.error(f"Error processing block {block_number}: {e}", exc_info=True)

# Process transactions for a specific blockchain and number of blocks
# Usage: await process_chain_by_recently_blocks("eth", 100, logger)
async def process_chain_by_recently_blocks(chain: str, blocks_to_fetch: int, logger: logging.Logger):
    try:
        service = ServiceFactory.get_service(chain)
        
        daily_transactions = await fetch_transactions(service, blocks_to_fetch)
        logger.info(f"Retrieved {len(daily_transactions)} transactions for {chain}")
        
        filtered_transactions = filter_transactions(daily_transactions)
        
        current_date = datetime.now().date()
        
        for tx in filtered_transactions:
            block_number = tx['block_number']
            save_to_csv([tx], chain, current_date, block_number)
        
        logger.info(f"Saved {len(filtered_transactions)} transactions for {chain}")
    except Exception as e:
        logger.error(f"Error processing {chain}: {e}")
        raise

# Process transactions for a specific blockchain within a date range
# Usage: await process_chain_by_date_range("eth", start_date, end_date, logger)
async def process_chain_by_date_range(chain: str, start_date: datetime, end_date: datetime, logger: logging.Logger, max_concurrent_days: int = 5, max_concurrent_blocks: int = 20):
    try:
        logger.info(f"Processing {chain} from {start_date.date()} to {end_date.date()}")
        service = ServiceFactory.get_service(chain)
        
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Use semaphore to limit concurrent block processing
        block_semaphore = Semaphore(max_concurrent_blocks)

        async def process_block(block_number: int, day: datetime):
            async with block_semaphore:
                try:
                    transactions = await service.get_transactions_for_single_block(block_number, day)
                    filtered_transactions = filter_transactions(transactions)
                    
                    if filtered_transactions:
                        save_to_csv(filtered_transactions, chain, day.date(), block_number)
                        logger.info(f"Saved {len(filtered_transactions)} transactions for block {block_number}")
                    else:
                        logger.info(f"No transactions to save for block {block_number}")
                except Exception as e:
                    logger.error(f"Error processing block {block_number}: {e}", exc_info=True)

        async def process_day(day: datetime):
            day_end = min(day.replace(hour=23, minute=59, second=59, microsecond=999999), end_date)
            start_block = await service.get_block_height_by_time(day, "after")
            end_block = await service.get_block_height_by_time(day_end, "before")
            
            logger.info(f"Fetching blocks for {day.date()} from {start_block} to {end_block}")
            
            block_tasks = [process_block(block_number, day) for block_number in range(start_block, end_block + 1)]
            await asyncio.gather(*block_tasks)

        async def process_days(days: List[datetime]):
            tasks = [process_day(day) for day in days]
            await asyncio.gather(*tasks)

        current_date = start_date
        while current_date <= end_date:
            days_to_process = []
            for _ in range(max_concurrent_days):
                if current_date <= end_date:
                    days_to_process.append(current_date)
                    current_date += timedelta(days=1)
                else:
                    break
            
            await process_days(days_to_process)

        logger.info(f"Completed processing {chain} from {start_date.date()} to {end_date.date()}")
        
    except Exception as e:
        logger.error(f"Error processing {chain}: {e}", exc_info=True)

async def main():
    logger = setup_logger("main", level=logging.INFO)
    
    # Example usage
    chain = "eth"
    start_date = datetime(2024, 9, 7)
    end_date = datetime(2024, 9, 7)
    
    try:
        await process_chain_by_date_range(chain, start_date, end_date, logger)
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())