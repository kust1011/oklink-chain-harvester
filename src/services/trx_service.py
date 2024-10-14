import httpx
from .base_service import BaseService

class TrxService(BaseService):
    CHAIN_NAME = "trx"

    def __init__(self, api_key, logger):
        super().__init__(api_key, logger)