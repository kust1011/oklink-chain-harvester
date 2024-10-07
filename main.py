import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from src.factory import ServiceFactory
from src.utils.utils import save_to_csv, setup_logger

# Fetch transactions for a given number of blocks
async def fetch_transactions(service, blocks_to_fetch: int) -> List[Dict]:
    return await service.get_latest_transactions(blocks_to_fetch)

# Filter and format transaction data
def filter_transactions(transactions: List[Dict]) -> List[Dict]:
    return [
        {
            'hash': tx.get('txid', ''),
            'block_hash': tx.get('blockHash', ''),
            'block_number': tx.get('height', ''),
            'from_address': tx.get('from', ''),
            'to_address': tx.get('to', ''),
            'value': tx.get('amount', ''),
            'gas': tx.get('txfee', ''),
            'block_timestamp': tx.get('transactionTime', ''),
        }
        for tx in transactions
    ]

# Process transactions for a specific blockchain and number of blocks
# Usage: await process_chain("eth", 100, logger)
async def process_chain(chain: str, blocks_to_fetch: int, logger: logging.Logger):
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
async def process_chain_by_date_range(chain: str, start_date: datetime, end_date: datetime, logger: logging.Logger):
    try:
        logger.info(f"Processing {chain} from {start_date.date()} to {end_date.date()}")
        service = ServiceFactory.get_service(chain)
        transactions = await service.get_transactions_by_date_range(start_date, end_date)
        logger.info(f"Retrieved {len(transactions)} transactions for {chain}")
        
        # Group transactions by date
        transactions_by_date = {}
        for tx in transactions:
            tx_date = datetime.fromtimestamp(int(tx['transactionTime']) / 1000).date()
            if tx_date not in transactions_by_date:
                transactions_by_date[tx_date] = []
            transactions_by_date[tx_date].append(tx)
        
        # Process and save transactions for each date
        for date, daily_transactions in transactions_by_date.items():
            filtered_transactions = filter_transactions(daily_transactions)
            
            # Save each transaction to a CSV file
            for tx in filtered_transactions:
                block_number = tx['block_number']
                save_to_csv([tx], chain, date, block_number)
            
            logger.info(f"Saved {len(filtered_transactions)} transactions for {chain} on {date}")
        
    except Exception as e:
        logger.error(f"Error processing {chain}: {e}", exc_info=True)

async def main():
    logger = setup_logger("main", level=logging.INFO)
    
    # Example usage
    chain = "eth"
    start_date = datetime(2024, 9, 30, 8, 0, 0, 0)
    end_date = datetime(2024, 9, 30, 8, 0, 20, 0)
    
    try:
        await process_chain_by_date_range(chain, start_date, end_date, logger)
        # await process_chain(chain, 2, logger)
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())