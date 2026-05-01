from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml


@dataclass(frozen=True)
class SourceSpec:
    name: str
    repo: str
    repo_last_commit_utc: str
    file_type: str
    url: str
    notes: str


def load_sources(config_path: Path) -> list[SourceSpec]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw_sources = payload.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ValueError("config.sources must be a list")

    sources: list[SourceSpec] = []
    for item in raw_sources:
        if not isinstance(item, dict):
            raise ValueError("each source entry must be a mapping")
        sources.append(
            SourceSpec(
                name=str(item["name"]),
                repo=str(item["repo"]),
                repo_last_commit_utc=str(item["repo_last_commit_utc"]),
                file_type=str(item["file_type"]),
                url=str(item["url"]),
                notes=str(item.get("notes", "")),
            )
        )
    return sources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import curated GitHub proxy sources through the dashboard API.",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="Base URL for the running ProxyPool Architect API.",
    )
    parser.add_argument(
        "--config",
        default="config/github_proxy_sources.yaml",
        help="YAML file containing the curated source list.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=10,
        help="How many raw proxies to print after imports complete.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Optional source name filter. Can be passed multiple times.",
    )
    return parser.parse_args()


async def fetch_json(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    response = await client.get(path)
    response.raise_for_status()
    return response.json()


async def import_source(
    client: httpx.AsyncClient,
    source: SourceSpec,
) -> dict[str, Any]:
    before = await fetch_json(client, "/stats")
    response = await client.post(
        "/providers/import-url",
        json={"url": source.url, "file_type": source.file_type},
    )
    response.raise_for_status()
    result = response.json()
    after = await fetch_json(client, "/stats")
    return {
        "source": source,
        "result": result,
        "total_before": int(before["total"]),
        "total_after": int(after["total"]),
        "raw_before": int(before["raw"]),
        "raw_after": int(after["raw"]),
    }


def print_import_report(report: dict[str, Any]) -> None:
    source = report["source"]
    result = report["result"]
    total_delta = report["total_after"] - report["total_before"]
    raw_delta = report["raw_after"] - report["raw_before"]

    print(f"\n[{source.name}]")
    print(f"repo: {source.repo}")
    print(f"repo_last_commit_utc: {source.repo_last_commit_utc}")
    print(f"url: {source.url}")
    print(f"file_type: {source.file_type}")
    print(f"notes: {source.notes}")
    print(
        "import_result: "
        f"fetched={result['fetched_count']} "
        f"valid={result['valid_count']} "
        f"stored={result['stored_count']} "
        f"duplicate={result['duplicate_count']} "
        f"invalid={result['invalid_count']} "
        f"direct={result['direct_supported_count']} "
        f"adapter_required={result['adapter_required_count']} "
        f"unsupported={result['unsupported_count']}"
    )
    print(f"pool_delta: total={total_delta:+d} raw={raw_delta:+d}")
    print(
        "detected: "
        f"format={result['detected_format']} "
        f"protocols={','.join(result['detected_protocols']) or '-'} "
        f"modes={','.join(result['supported_connection_modes']) or '-'}"
    )


def print_sample(items: list[dict[str, Any]]) -> None:
    print("\n[sample raw proxies]")
    if not items:
        print("no raw proxies returned")
        return

    for item in items:
        print(
            f"{item['id']} "
            f"scheme={item['scheme']} "
            f"host={item['host']} "
            f"port={item['port']} "
            f"source={item['source']} "
            f"anonymity={item['anonymity']} "
            f"status={item['status']}"
        )


async def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    sources = load_sources(config_path)
    if args.source:
        wanted = {name.casefold() for name in args.source}
        sources = [source for source in sources if source.name.casefold() in wanted]
    if not sources:
        raise SystemExit("no sources selected")

    async with httpx.AsyncClient(
        base_url=args.api_base.rstrip("/"),
        timeout=httpx.Timeout(60.0),
        follow_redirects=False,
    ) as client:
        health = await fetch_json(client, "/health")
        print(
            "api_health: "
            f"status={health['status']} redis={health['redis']} scheduler={health['scheduler']}"
        )

        for source in sources:
            report = await import_source(client, source)
            print_import_report(report)

        stats = await fetch_json(client, "/stats")
        print(
            "\n[pool totals]\n"
            f"raw={stats['raw']} checked={stats['checked']} elite={stats['elite']} "
            f"dead={stats['dead']} cooldown={stats['cooldown']} total={stats['total']}"
        )
        proxy_list = await fetch_json(
            client,
            f"/proxy/list?pool=raw&limit={args.sample_limit}&offset=0",
        )
        print_sample(proxy_list.get("items", []))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
