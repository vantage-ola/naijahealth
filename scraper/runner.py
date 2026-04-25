"""CLI entry point for running NAFDAC scraper spiders."""

import asyncio
import json
import logging
import sys
from pathlib import Path

from core.config import get_config

SPIDERS = {
    "greenbook": "scraper.spiders.drugs",
    "food": "scraper.spiders.food",
    "herbal": "scraper.spiders.herbal",
}


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )


async def _run_spider(name: str, output_dir: Path) -> int:
    module = __import__(SPIDERS[name], fromlist=["crawl"])
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{name}.jsonl"

    count = 0
    with open(out_path, "w") as f:
        async for product in module.crawl():
            f.write(product.model_dump_json() + "\n")
            count += 1

    logging.getLogger(__name__).info("%s: wrote %d records to %s", name, count, out_path)
    return count


async def run(names: list[str], output_dir: Path) -> dict[str, int]:
    results = {}
    for name in names:
        if name not in SPIDERS:
            logging.getLogger(__name__).error("unknown spider: %s (available: %s)", name, ", ".join(SPIDERS))
            continue
        results[name] = await _run_spider(name, output_dir)
    return results


def main() -> None:
    args = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    args = [a for a in args if a not in ("--verbose", "-v")]

    _setup_logging(verbose)

    config = get_config()
    output_dir = Path(config.scraper_output_dir)

    if not args or args == ["all"]:
        names = list(SPIDERS.keys())
    else:
        names = args

    results = asyncio.run(run(names, output_dir))
    total = sum(results.values())
    print(json.dumps({"spiders": results, "total": total}, indent=2))


if __name__ == "__main__":
    main()
