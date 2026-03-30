#!/usr/bin/env python3
"""Classify MaxMind ASN records into EDU/GOV buckets."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Optional


EDU_KEYWORDS = [
    "univ",
    "university",
    "college",
    "institute",
    "school",
    "academy",
    "polytechnic",
    "campus",
    "faculty",
    "research",
    ".edu",
]

GOV_KEYWORDS = [
    "gov",
    "government",
    "ministry",
    "department",
    "agency",
    "municipal",
    "state of",
    "city of",
    "county of",
    "federal",
    "national",
    "parliament",
    "senate",
    ".gov",
]

NEGATIVE_KEYWORDS = [
    "cloud",
    "hosting",
    "telecom",
    "communications",
    "broadband",
    "wireless",
    "vpn",
    "cdn",
    "data center",
    "datacenter",
]


EDU_WEIGHT: Dict[str, int] = {
    "univ": 3,
    "university": 3,
    "college": 3,
    "institute": 2,
    "school": 2,
    "academy": 2,
    "polytechnic": 2,
    "campus": 1,
    "faculty": 1,
    "research": 1,
    ".edu": 5,
}

GOV_WEIGHT: Dict[str, int] = {
    "gov": 4,
    "government": 4,
    "ministry": 3,
    "department": 3,
    "agency": 2,
    "municipal": 2,
    "state of": 2,
    "city of": 2,
    "county of": 2,
    "federal": 3,
    "national": 2,
    "parliament": 3,
    "senate": 3,
    ".gov": 5,
}


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[^a-z0-9\.\-\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def score_keywords(text: str, keywords: list[str], weight_map: Dict[str, int]) -> int:
    score = 0
    for kw in keywords:
        if kw in text:
            score += weight_map.get(kw, 1)
    return score


def classify_as_org(org_name: str) -> Optional[str]:
    text = normalize_text(org_name)

    edu_score = score_keywords(text, EDU_KEYWORDS, EDU_WEIGHT)
    gov_score = score_keywords(text, GOV_KEYWORDS, GOV_WEIGHT)

    negative_score = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    edu_score -= negative_score
    gov_score -= negative_score

    if gov_score >= 3 and gov_score > edu_score:
        return "gov"

    if edu_score >= 3 and edu_score >= gov_score:
        return "edu"

    return None


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["asn", "org", "network"])
        writer.writeheader()
        writer.writerows(rows)


def extract_edu_gov_asn(input_csv: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    edu_rows: list[dict[str, str]] = []
    gov_rows: list[dict[str, str]] = []

    with input_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            network = row["network"]
            asn = row["autonomous_system_number"]
            org = row["autonomous_system_organization"]

            category = classify_as_org(org)
            if category is None:
                continue

            target = edu_rows if category == "edu" else gov_rows
            target.append({"asn": asn, "org": org, "network": network})

    return edu_rows, gov_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Classify MaxMind ASN IPv4 records into edu/gov using "
            "keyword scoring and negative-word suppression."
        )
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default="GeoLite2-ASN-Blocks-IPv4.csv",
        help="Path to MaxMind GeoLite2 ASN IPv4 CSV.",
    )
    parser.add_argument(
        "--edu-output",
        default="edu_asn.csv",
        help="Output file for edu rows.",
    )
    parser.add_argument(
        "--gov-output",
        default="gov_asn.csv",
        help="Output file for gov rows.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    edu_output = Path(args.edu_output)
    gov_output = Path(args.gov_output)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    edu_rows, gov_rows = extract_edu_gov_asn(input_csv)

    write_rows(edu_output, edu_rows)
    write_rows(gov_output, gov_rows)

    print(f"EDU rows: {len(edu_rows)} -> {edu_output}")
    print(f"GOV rows: {len(gov_rows)} -> {gov_output}")


if __name__ == "__main__":
    main()
