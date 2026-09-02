from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from england_experiment import finalize_outputs, run_experiment
from terrain_sources import EA_DTM_COVERAGE_ID, EA_DTM_WCS_URL, EAWcsBlockCache


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the private, bounded England high-resolution terrain experiment."
    )
    parser.add_argument("--gpx-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--wales-results", type=Path, required=True)
    return parser.parse_args()


def _request_xml(parameters: list[tuple[str, str]]) -> tuple[ET.Element, int]:
    url = EA_DTM_WCS_URL + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(
        url, headers={"User-Agent": "Meridian terrain research/2"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(100_000)
        if response.status != 200 or response.headers.get_content_type() not in {
            "application/xml",
            "text/xml",
        }:
            raise RuntimeError("Unexpected EA WCS metadata response")
    return ET.fromstring(payload), len(payload)


def preflight(output_root: Path) -> dict[str, object]:
    capabilities, capabilities_bytes = _request_xml(
        [("service", "WCS"), ("version", "2.0.1"), ("request", "GetCapabilities")]
    )
    describe, describe_bytes = _request_xml(
        [
            ("service", "WCS"),
            ("version", "2.0.1"),
            ("request", "DescribeCoverage"),
            ("coverageId", EA_DTM_COVERAGE_ID),
        ]
    )
    coverage_ids = {
        element.text
        for element in capabilities.iter()
        if element.tag.endswith("CoverageId")
    }
    if EA_DTM_COVERAGE_ID not in coverage_ids:
        raise RuntimeError("Expected EA DTM coverage is not advertised")
    description = ET.tostring(describe, encoding="unicode")
    values_by_tag = {
        element.tag.rsplit("}", 1)[-1]: (element.text or "").strip()
        for element in describe.iter()
    }
    if "EPSG/0/27700" not in description:
        raise RuntimeError("EA WCS description has an unexpected CRS")
    if values_by_tag.get("low") != "0 0" or values_by_tag.get("high") != "575999 660999":
        raise RuntimeError("EA WCS description has unexpected grid bounds")
    source = EAWcsBlockCache(output_root / "cache" / "ea-wcs")
    tiny = source.probe_projected(530_005.0, 180_005.0, 10)
    return {
        "capabilities_bytes": capabilities_bytes,
        "describe_coverage_bytes": describe_bytes,
        "coverage_id": EA_DTM_COVERAGE_ID,
        "tiny_subset": tiny,
        "tiny_subset_crs": "EPSG:27700",
        "tiny_subset_shape": [10, 10],
        "tiny_subset_dtype": "float32",
        "tiny_subset_nodata": source.metadata.nodata,
    }


def main() -> None:
    arguments = parse_arguments()
    output_root = arguments.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    for child in ("cache", "reports", "plots", "derived"):
        (output_root / child).mkdir(exist_ok=True)
    checked = preflight(output_root)
    results = run_experiment(
        arguments.gpx_root,
        output_root,
        arguments.repo_root,
        arguments.wales_results,
        checked,
    )
    finalize_outputs(output_root, arguments.wales_results)
    print(
        json.dumps(
            {
                "routes": results["discovery"]["confirmed_route_names"],
                "rejected_by_safety_limit": results["discovery"]["rejected_by_route_block_limit"],
                "network_bytes": results["cache"]["ea"]["downloaded_bytes"],
                "cache_bytes": results["cache"]["ea"]["cache_bytes"],
                "runtime_seconds": results["runtime_seconds"],
                "report": str(output_root / "reports" / "summary.md"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
