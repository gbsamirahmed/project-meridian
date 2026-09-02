from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from terrain_sources import WELSH_DTM_URL, configure_gdal_environment
from wales_experiment import finalize_outputs, run_experiment


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the private, bounded Welsh high-resolution terrain experiment."
    )
    parser.add_argument("--gpx-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def http_preflight() -> dict[str, object]:
    headers = {"User-Agent": "Meridian terrain research/1"}
    head = urllib.request.Request(WELSH_DTM_URL, headers=headers, method="HEAD")
    with urllib.request.urlopen(head, timeout=30) as response:
        head_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower()
            in {
                "content-length",
                "content-type",
                "etag",
                "last-modified",
                "accept-ranges",
                "x-ms-blob-type",
            }
        }
        head_status = response.status
    ranged = urllib.request.Request(
        WELSH_DTM_URL,
        headers={**headers, "Range": "bytes=0-16383"},
        method="GET",
    )
    with urllib.request.urlopen(ranged, timeout=30) as response:
        if response.status != 206:
            raise RuntimeError(
                f"Welsh COG ignored the bounded range request (HTTP {response.status})"
            )
        payload = response.read(16_385)
        if len(payload) != 16_384:
            raise RuntimeError(f"Unexpected preflight range length: {len(payload)}")
        content_range = response.headers.get("Content-Range")
    return {
        "head_status": head_status,
        "headers": head_headers,
        "range_status": 206,
        "range_content": content_range,
        "range_bytes": len(payload),
        "bigtiff_header": payload[:4].hex().upper(),
    }


def _worker_command(arguments: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--gpx-root",
        str(arguments.gpx_root.resolve()),
        "--output-root",
        str(arguments.output_root.resolve()),
        "--repo-root",
        str(arguments.repo_root.resolve()),
    ]


def _network_from_curl_log(stderr: str) -> dict[str, int | bool]:
    status: int | None = None
    bytes_transferred = 0
    partial_requests = 0
    object_content_length = 0
    for line in stderr.splitlines():
        status_match = re.match(r"^< HTTP/\S+ (\d{3})", line)
        if status_match:
            status = int(status_match.group(1))
            if status == 206:
                partial_requests += 1
            continue
        length_match = re.match(r"^< Content-Length:\s*(\d+)", line, re.IGNORECASE)
        if length_match:
            length = int(length_match.group(1))
            if status == 206:
                bytes_transferred += length
            elif status == 200:
                object_content_length = max(object_content_length, length)
    return {
        "partial_requests": partial_requests,
        "bytes_transferred": bytes_transferred,
        "object_content_length": object_content_length,
        "range_access_observed": partial_requests > 0,
    }


def main() -> None:
    arguments = parse_arguments()
    configure_gdal_environment()
    if arguments.worker:
        run_experiment(arguments.gpx_root, arguments.output_root, arguments.repo_root)
        return

    preflight = http_preflight()
    environment = os.environ.copy()
    environment["CPL_CURL_VERBOSE"] = "YES"
    started = time.perf_counter()
    process = subprocess.run(
        _worker_command(arguments),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.stdout:
        print(process.stdout, end="")
    if process.returncode != 0:
        if process.stderr:
            print(process.stderr, file=sys.stderr)
        raise SystemExit(process.returncode)
    network = _network_from_curl_log(process.stderr)
    network["preflight"] = preflight
    network["preflight_range_bytes"] = preflight["range_bytes"]
    network["bytes_transferred"] = int(network["bytes_transferred"]) + int(
        preflight["range_bytes"]
    )
    network["wrapper_seconds"] = 0.0
    results = finalize_outputs(arguments.output_root.resolve(), network)
    print(
        json.dumps(
            {
                "routes": results["discovery"]["confirmed_route_names"],
                "network_bytes": results["network"]["bytes_transferred"],
                "cache_bytes": results["cache"]["welsh_cache_bytes"],
                "runtime_seconds": results["runtime_seconds"],
                "report": str(arguments.output_root.resolve() / "reports" / "summary.md"),
                "wall_seconds": time.perf_counter() - started,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
