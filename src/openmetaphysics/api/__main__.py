"""CLI entry: run the API with uvicorn."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("openmetaphysics.api.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
