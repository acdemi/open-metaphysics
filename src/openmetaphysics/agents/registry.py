"""Agent registry — the single discovery/extension point."""

from __future__ import annotations

from ..core.engines import BaseAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise KeyError(f"unknown agent: {name}; available: {list(self._agents)}")
        return self._agents[name]

    def all(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def names(self) -> list[str]:
        return list(self._agents.keys())

    def schemas(self) -> dict[str, dict]:
        return {n: a.schema() for n, a in self._agents.items()}


_default: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _default
    if _default is None:
        _default = AgentRegistry()
        # import here to avoid circular imports at module load
        from .bazi import BaziAgent
        from .liuyao import LiuyaoAgent
        from .qimen import QimenAgent
        from .ziwei import ZiweiAgent

        for agent in (BaziAgent(), LiuyaoAgent(), QimenAgent(), ZiweiAgent()):
            _default.register(agent)
    return _default


def reset_registry() -> None:
    global _default
    _default = None
