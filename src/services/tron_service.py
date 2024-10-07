import httpx
from .base_service import BaseService

class TronService(BaseService):
    CHAIN_NAME = "tron"

    def __init__(self, api_key, logger):
        super().__init__(api_key, logger)