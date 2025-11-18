"""CLI demo for the clinical summary extractor."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from .aggregator import ClinicalSummaryExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_demo(note_path: Path, pretty: bool = False) -> None:
    load_dotenv()

    if not note_path.exists():
        raise FileNotFoundError(f"Clinical note not found: {note_path}")

    clinical_text = note_path.read_text()
    extractor = ClinicalSummaryExtractor()

    logger.info("Running clinical summary extraction on %s", note_path)
    result = await extractor.extract(clinical_text)

    output = result.model_dump()
    if pretty:
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output))


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo the clinical summary extractor.")
    parser.add_argument(
        "--note",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "test.txt",
        help="Path to clinical note text file (default: project test.txt)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()
    asyncio.run(run_demo(args.note, args.pretty))


if __name__ == "__main__":
    main()

