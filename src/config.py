import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

def get_api_keys(prefix: str) -> List[str]:
    keys = []
    i = 0
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
    "trx": get_api_keys("OKLINK_TRX_KEY"),
    "eth": get_api_keys("OKLINK_ETH_KEY")
}