# Python Packages

This directory hosts future Python service packages (e.g., Explain Agent, RAG Retriever, DSL Parser).

The existing Python package `openmetaphysics` lives at `src/openmetaphysics/` (managed by root `pyproject.toml`).

## Structure (planned)

```
python/
├── explain-agent/     # Explain Agent gRPC service (Phase 9+)
├── rag-retriever/     # RAG Retriever service (Phase 9+)
└── proto_gen/         # Auto-generated protobuf Python code
```

See: docs/engineering/14_polyglot_architecture.md (Python Layer)
