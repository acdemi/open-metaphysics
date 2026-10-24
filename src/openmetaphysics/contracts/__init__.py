"""Contract adapters (machine-verifiable).

机器可验证的适配层: 各域 Behavior Contract v1.0.0 ↔ Runtime。
不修改运行时; 仅提供契约校验能力。
"""

from .consensus_contract import ConsensusContractAdapter
from .qimen_contract import MANIFEST, QimenContractAdapter, __version__

__all__ = [
    "ConsensusContractAdapter",
    "MANIFEST",
    "QimenContractAdapter",
    "__version__",
]
