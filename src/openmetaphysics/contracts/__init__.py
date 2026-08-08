"""Qimen Contract Adapter (Phase 5.8).

机器可验证的适配层: Qimen Behavior Contract v1.0.0 ↔ Runtime。
不修改运行时; 仅提供契约校验能力。
"""

from .qimen_contract import MANIFEST, QimenContractAdapter, __version__

__all__ = ["MANIFEST", "QimenContractAdapter", "__version__"]
