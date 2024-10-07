from typing import Dict, Type, List
from src.services.base_service import BaseService
from src.services.eth_service import EthService
from src.services.btc_service import BtcService
from src.services.tron_service import TronService
from src.config import OKLINK_KEY_MAPPING
from src.utils.utils import setup_logger

class ServiceFactory:
    _services: Dict[str, Type[BaseService]] = {
        "eth": EthService,
        "btc": BtcService,
        "tron": TronService
    }

    @classmethod
    def get_service(cls, chain_name: str) -> BaseService:
        service_class = cls._services.get(chain_name)
        if not service_class:
            raise ValueError(f"Unsupported chain: {chain_name}")
        
        api_keys = OKLINK_KEY_MAPPING.get(chain_name, [])
        if not api_keys:
            raise ValueError(f"No API keys found for chain: {chain_name}")
        
        logger = setup_logger(f"{chain_name}_service")
        return service_class(api_keys, logger)