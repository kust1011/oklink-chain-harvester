import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

def get_api_keys(prefix: str) -> List[str]:
    keys = []
    i = 1
    while True:
        key = os.getenv(f"{prefix}_{i}")
        if key:
            keys.append(key)
            i += 1
        else:
            break
    return keys

OKLINK_KEY_MAPPING = {
    "btc": get_api_keys("OKLINK_BTC_KEY"),
    "tron": get_api_keys("OKLINK_TRON_KEY"),
    "eth": get_api_keys("OKLINK_ETH_KEY")
}