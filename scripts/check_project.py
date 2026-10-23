#!/usr/bin/env python3
"""Check current project links, selected evidence and optional archive integrity."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import runpy
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "legacy/2026-10-23_project_reset"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check(include_archive=False):
    errors = []
    info = {}

    def require(condition, message):
        if not condition:
            errors.append(message)

    active = sorted(p for p in ROOT.rglob("*") if p.is_file()
                    and not {"legacy", ".git"}.intersection(p.relative_to(ROOT).parts))
    info["active_files"] = len(active)
    info["active_bytes"] = sum(p.stat().st_size for p in active)
    require(all(str(p.relative_to(ROOT)).isascii() for p in active), "Non-English active path")
    require(not any("__pycache__" in p.parts for p in active), "Active Python cache found")
    authored = [p for p in active if p.suffix == ".md"] + [ROOT / "docs/reports/research_report.html"]
    renderer = MarkdownIt("commonmark").enable("table")
    links = 0
    for p in authored:
        if not p.exists():
            require(False, f"Missing document: {p}")
            continue
        content = p.read_text(encoding="utf-8")
        soup = BeautifulSoup(renderer.render(content) if p.suffix == ".md" else content, "html.parser")
        for tag in soup.select("a[href], img[src]"):
            link = tag.get("href", tag.get("src"))
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            links += 1
            target = (p.parent / unquote(parts.path)).resolve() if parts.path else p
            require(target.exists(), f"Broken link in {p.relative_to(ROOT)}: {link}")
            if parts.fragment and target.exists() and target.suffix == ".html":
                target_soup = soup if target == p else BeautifulSoup(target.read_text(), "html.parser")
                require(target_soup.find(id=unquote(parts.fragment)) is not None, f"Missing anchor: {link}")
    info["local_links_checked"] = links
    namespace = runpy.run_path(str(ROOT / "scripts/build_report.py"))
    html = ROOT / "docs/reports/research_report.html"
    require(html.exists() and html.read_text() == namespace["render"](), "Report HTML is out of date")
    for p in active:
        if p.suffix == ".json":
            try:
                json.loads(p.read_text(encoding="utf-8-sig"))
            except (ValueError, UnicodeError) as exc:
                require(False, f"Invalid JSON {p.relative_to(ROOT)}: {exc}")
    catalog = rows(ROOT / "docs/model_catalog.csv")
    require(len(catalog) == 8, "Expected eight baseline models")
    for row in catalog:
        for field in ("pkml", "snapshot", "reference"):
            require((ROOT / row[field]).is_file(), f"Missing {field} for {row['name']}")
        path = ROOT / row["pkml"]
        if path.exists():
            try:
                xml = ET.fromstring(gzip.decompress(path.read_bytes()))
                require(xml.tag == "SimulationTransfer" and xml.find("Simulation") is not None,
                        f"Invalid PKML model: {path}")
            except (OSError, ET.ParseError) as exc:
                require(False, f"Unreadable PKML: {path}: {exc}")
    info["baseline_models"] = len(catalog)
    snapshot = json.loads((ROOT / "DXM/models/osp/dxm_snapshot.json").read_text())
    for key, expected in (("Compounds", 3), ("Simulations", 29), ("ObservedData", 41)):
        require(len(snapshot[key]) == expected, f"DXM snapshot count: {key}")
    index = rows(ROOT / "DXM/data/observations/dataset_index.csv")
    observations = rows(ROOT / "DXM/data/observations/observations.csv")
    require(len(index) == 41 and sum(int(r["timepoints"]) for r in index) == 393,
            "DXM dataset index counts changed")
    require(len(observations) == 732, "DXM observation row count changed")
    for dataset in index:
        primary = [r for r in observations if r["dataset_id"] == dataset["dataset_id"] and r["role"] == "primary"]
        require(len({r["point_index"] for r in primary}) == int(dataset["timepoints"]),
                f"Observation count mismatch: {dataset['dataset_id']}")
        require(dataset["data_file"] == "observations.csv", "Stale dataset file pointer")
    observed = rows(ROOT / "MCT/data/parent_pk/observed_digitized.csv")
    curves = rows(ROOT / "MCT/results/baseline_curves.csv")
    require(len(observed) == 14, "MCT approximate observations count changed")
    require(len(curves) == 1010 and {r["scenario"] for r in curves} == {"baseline"}
            and {r["mode"] for r in curves} == {"pkml_rerun"}, "MCT baseline selection changed")
    info["evidence_counts"] = {"dxm_datasets":len(index), "dxm_timepoints":393,
        "dxm_long_rows":len(observations), "mct_digitized_points":len(observed), "mct_baseline_rows":len(curves)}
    structures = 0
    for case in ("DXM", "MCT"):
        manifest = json.loads((ROOT / case / "structures/sources.json").read_text())
        for item in manifest["files"]:
            path = ROOT / item["file"]
            require(path.exists() and sha256(path) == item["sha256"], f"Structure source hash: {item['file']}")
            structures += 1
    info["structure_hashes_checked"] = structures
    if include_archive:
        original = json.loads((ARCHIVE / "original_files.json").read_text())
        for item in original:
            path = ARCHIVE / item["original_path"]
            require(path.exists() and path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"],
                    f"Archive integrity: {item['original_path']}")
        selected = json.loads((ARCHIVE / "active_file_origins.json").read_text())
        for item in selected:
            path = ROOT / item["active_path"]
            require(path.exists() and sha256(path) == item["active_sha256"], f"Selected evidence hash: {item['active_path']}")
            source = ARCHIVE / item["original_path"]
            require(source.exists() and sha256(source) == item["source_sha256"], f"Selected source: {item['original_path']}")
            if item["operation"] == "copy" and path.exists() and source.exists():
                require(path.read_bytes() == source.read_bytes(), f"Copy differs: {item['active_path']}")
            elif item["active_path"].endswith(".pkml.gz"):
                require(gzip.decompress(path.read_bytes()) == source.read_bytes(), f"PKML compression differs: {item['active_path']}")
        info["archived_original_hashes_checked"] = len(original)
        info["selected_origins_checked"] = len(selected)
    info["errors"] = errors
    info["status"] = "pass" if not errors else "fail"
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", action="store_true", help="Also hash all preserved original files")
    result = check(parser.parse_args().archive)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["errors"]))
