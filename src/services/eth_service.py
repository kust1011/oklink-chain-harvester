import httpx
from .base_service import BaseService

class EthService(BaseService):
    CHAIN_NAME = "eth"

    def __init__(self, api_key, logger):
        super().__init__(api_key, logger)