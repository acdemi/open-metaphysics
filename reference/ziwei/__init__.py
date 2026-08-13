"""Reference Ziwei domain package.

Independent implementation of docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md
(BC-001~014, Engine v0.3.0 behavior). No src/ imports; shared normative
calendar primitives are reused from reference/bazi/* with citations.
"""

from .domain import ZiweiReferenceInput, compute

__all__ = ["ZiweiReferenceInput", "compute"]
