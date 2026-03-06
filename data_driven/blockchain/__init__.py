# -*- coding: utf-8 -*-
"""
区块链存证模块

包含：哈希计算、存证合约、验真模块
"""

__version__ = "1.0.0"

from .hash import HashComputer
from .contract import ChainRecord, ChainContract, DictStorageAdapter
from .verify import ChainVerifier, MockChainStorage, VerifyResult
from .web3_client import Web3Client

__all__ = [
    "HashComputer",
    "ChainRecord",
    "ChainContract", 
    "DictStorageAdapter",
    "ChainVerifier",
    "MockChainStorage",
    "VerifyResult",
    "Web3Client",
]
