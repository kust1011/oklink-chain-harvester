import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.factory import ServiceFactory
from src.services.eth_service import EthService
from datetime import datetime

@pytest.fixture
def eth_service():
    return ServiceFactory.get_service("eth")

@pytest.mark.asyncio
async def test_get_latest_block_number(eth_service):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{'height': '12345678', 'blockTime': '987654321'}]
        }
        mock_get.return_value = mock_response

        block_number = await eth_service.get_latest_block_number()
        assert block_number == 12345678

@pytest.mark.asyncio
async def test_get_transactions_for_single_block(eth_service):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{
                "page": "1",
                "limit": "100",
                "totalPage": "1",
                "blockList": [
                    {
                        "txid": "0x123...",
                        "height": "12345678",
                        "from": "0xabc...",
                        "to": "0xdef...",
                        "amount": "1.23",
                        "transactionTime": "1630000000000"
                    }
                ]
            }]
        }
        mock_get.return_value = mock_response

        test_date = datetime.now()
        transactions = await eth_service.get_transactions_for_single_block(12345678, test_date)
        
        assert len(transactions) == 1
        assert transactions[0]['txid'] == "0x123..."

@pytest.mark.asyncio
async def test_get_latest_transactions(eth_service):
    with patch.object(EthService, 'get_latest_block_number', return_value=12345678), \
         patch.object(EthService, 'get_transactions_for_single_block', return_value=[{'txid': '0x123...'}]):
        
        transactions = await eth_service.get_latest_transactions(1)
        assert len(transactions) == 1
        assert transactions[0]['txid'] == "0x123..."
        assert transactions[0]['blockNumber'] == 12345678

@pytest.mark.asyncio
async def test_error_handling(eth_service):
    with patch('httpx.AsyncClient.get', side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc_info:
            await eth_service.get_latest_block_number()
        assert str(exc_info.value) == "API Error"

# Integration test
@pytest.mark.asyncio
async def test_full_flow():
    service = ServiceFactory.get_service("eth")
    try:
        latest_block = await service.get_latest_block_number()
        assert isinstance(latest_block, int)
        assert latest_block > 0

        test_date = datetime.now()
        transactions = await service.get_transactions_for_single_block(latest_block, test_date)
        
        assert isinstance(transactions, list)
        if transactions:
            assert 'txid' in transactions[0]
            assert 'from' in transactions[0]
            assert 'to' in transactions[0]
    except Exception as e:
        pytest.fail(f"Integration test failed: {str(e)}")