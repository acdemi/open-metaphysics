"""H4 regression: Explain retrieval must stay inside the output agent's domain.

Review H4: ``Explainer.retrieve`` pooled the four frozen corpora in one retriever
and returned the raw top-k, so a Ziwei explanation cited BaZi ``shen_sha``
knowledge (chunk ids ``kn:shen_sha:*`` carrying the ``bazi`` tag).

The fix restores the domain filter already present on ``main`` (commit
``e84464d``): over-fetch candidates, keep the chunks whose tags contain
``output.agent``, and fall back to the unfiltered list only when the domain is
sparse (no domain-tagged candidate at all). ``/knowledge/search`` keeps its
cross-domain behaviour and is asserted to stay unfiltered.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from openmetaphysics.agents.registry import get_registry
from openmetaphysics.api.app import create_app
from openmetaphysics.core.schemas import Gender
from openmetaphysics.inference.explainer import Explainer, get_explainer_for
from openmetaphysics.rag.corpus import load_all_chunks
from openmetaphysics.rag.retriever import KnowledgeChunk, search_knowledge

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
DOMAINS = {"bazi", "ziwei", "qimen", "liuyao"}
AGENTS = ("bazi", "ziwei", "qimen", "liuyao")

PAYLOADS = {
    "bazi": {"request_id": "h4-domain", "born_at": BORN, "gender": Gender.MALE},
    "ziwei": {"request_id": "h4-domain", "born_at": BORN, "gender": Gender.MALE},
    "qimen": {"request_id": "h4-domain", "born_at": BORN, "gender": Gender.MALE},
    "liuyao": {
        "request_id": "h4-domain",
        "born_at": BORN,
        "gender": Gender.MALE,
        "seed": 42,
    },
}


def _output(agent_name: str):
    agent = get_registry().get(agent_name)
    return agent.compute(agent.input_schema.model_validate(PAYLOADS[agent_name]))


def _retrieve(agent_name: str, k: int = 5) -> list[KnowledgeChunk]:
    return get_explainer_for(agent_name).retrieve(_output(agent_name), k=k)


# -- the reported Ziwei -> BaZi leak ----------------------------------------


def test_ziwei_explain_no_longer_cites_bazi_shen_sha():
    chunks = _retrieve("ziwei", k=5)
    assert len(chunks) == 5
    assert all("ziwei" in chunk.tags for chunk in chunks), [c.tags for c in chunks]

    bazi_shen_sha = [chunk for chunk in chunks if "bazi" in chunk.tags and "shen_sha" in chunk.tags]
    assert not bazi_shen_sha, f"cross-domain shen_sha:bazi leakage: {bazi_shen_sha}"
    assert not any("bazi" in chunk.tags for chunk in chunks)


def test_explain_retrieval_stays_in_its_own_domain():
    for agent_name in AGENTS:
        chunks = _retrieve(agent_name, k=5)
        assert chunks, f"{agent_name}: no knowledge retrieved"
        assert all(agent_name in chunk.tags for chunk in chunks), (
            f"{agent_name}: foreign chunks {[c.id for c in chunks if agent_name not in c.tags]}"
        )
        foreign_tags = {tag for chunk in chunks for tag in DOMAINS & set(chunk.tags)}
        assert foreign_tags == {agent_name}, f"{agent_name}: mixed domains {foreign_tags}"


def test_ziwei_explain_payload_cites_only_ziwei_knowledge():
    output = _output("ziwei")
    result = get_explainer_for("ziwei").explain(output, k=5)
    assert result["knowledge"], "the explain chain must cite knowledge"

    index = {chunk.id: chunk for chunk in load_all_chunks()}
    for citation in result["knowledge"]:
        chunk = index[citation["id"]]
        assert "ziwei" in chunk.tags, citation
        assert "bazi" not in chunk.tags, citation


# -- documented degradation for a sparse / single-domain corpus -------------


class _BaziOnlyRetriever:
    """Stand-in for a corpus where the output's own domain has no chunks."""

    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]:
        return [
            KnowledgeChunk(
                id="kn:shen_sha:only_bazi",
                text="天乙贵人",
                source="三命通会",
                tags=["shen_sha", "bazi"],
            )
        ]


def test_sparse_domain_degrades_to_unfiltered_context():
    chunks = Explainer(retriever=_BaziOnlyRetriever()).retrieve(_output("ziwei"), k=3)
    assert [chunk.id for chunk in chunks] == ["kn:shen_sha:only_bazi"]


# -- /knowledge/search keeps cross-domain retrieval -------------------------


def test_knowledge_search_keeps_cross_domain_retrieval():
    chunks = search_knowledge("贵人", k=10)
    domains = {tag for chunk in chunks for tag in DOMAINS & set(chunk.tags)}
    assert "bazi" in domains, "bazi knowledge must stay searchable outside explain"
    assert len(domains) >= 2, f"search must stay cross-domain, got only {domains}"


def test_knowledge_search_endpoint_is_not_domain_filtered():
    client = TestClient(create_app())
    response = client.post("/knowledge/search", json={"query": "贵人", "k": 10})
    assert response.status_code == 200, response.text
    chunks = response.json()["chunks"]
    domains = {tag for chunk in chunks for tag in DOMAINS & set(chunk.get("tags", []))}
    assert "bazi" in domains
    assert len(domains) >= 2, f"endpoint must stay cross-domain, got only {domains}"
