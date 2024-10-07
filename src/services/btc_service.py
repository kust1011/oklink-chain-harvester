import httpx
from .base_service import BaseService

class BtcService(BaseService):
    CHAIN_NAME = "btc"

    def __init__(self, api_key, logger):
        super().__init__(api_key, logger)