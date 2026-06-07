"""
Build-time SNOMED CT subset fetcher.

Reads injury targets from seed.py PERSONAS (via snomedct_hint + affected_joints),
resolves each label against the public NCI EVS REST API, validates that the
resolved disorder's Finding Site maps to one of our 9 catalog joints, and writes
the result to backend/data/snomed_subset.json.

Run once; commit the output.

Usage:
    cd backend
    python scripts/build_snomed_subset.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

# ── paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = BACKEND_ROOT / "data" / "snomed_subset.json"

sys.path.insert(0, str(BACKEND_ROOT))

BASE = "https://api-evsrest.nci.nih.gov/api/v1/concept/snomedct_us"
_SLEEP = 0.3   # seconds between API calls — well under rate limit


def _get(url: str, **params) -> dict | list:
    resp = httpx.get(url, params=params, timeout=15)
    resp.raise_for_status()
    time.sleep(_SLEEP)
    return resp.json()


# ── 9 catalog joints ───────────────────────────────────────────────────────
# Hand-verified against NCI EVS snomedct_us. Stable — only change if the
# exercise catalog adds new joints_loaded values.
JOINT_MAP: dict[str, dict] = {
    "knee":           {"code": "49076000",  "skos": "exactMatch"},
    "shoulder":       {"code": "182168000", "skos": "exactMatch"},
    "hip":            {"code": "24136001",  "skos": "exactMatch"},
    "elbow":          {"code": "76248009",  "skos": "exactMatch"},
    "ankle":          {"code": "70258002",  "skos": "exactMatch"},
    "wrist":          {"code": "74670003",  "skos": "exactMatch"},
    "lumbar spine":   {"code": "122496007", "skos": "closeMatch"},
    "thoracic spine": {"code": "122495006", "skos": "closeMatch"},
    "cervical spine": {"code": "122494005", "skos": "closeMatch"},
}

# Pin codes where auto-resolution is ambiguous
CODE_OVERRIDES: dict[str, str] = {
    "Patellofemoral pain syndrome": "430725003",
    "Lumbar muscle strain": "300956001",  # "Low back strain" — better SNOMED coverage than generic muscle strain
}

_JOINT_CODES = {v["code"] for v in JOINT_MAP.values()}

# Keyword patterns for each catalog joint, matched case-insensitively against
# the relatedName of an RO association.  Covers tendon/bursa/bone structures
# that are anatomically at a joint but not hierarchically under it in SNOMED.
_JOINT_KEYWORDS: dict[str, list[str]] = {
    "knee":           ["knee", "patellar", "patellofemoral", "meniscus", "cruciate", "popliteal"],
    "shoulder":       ["shoulder", "subacromial", "rotator cuff", "glenohumeral", "acromioclavicular", "subscapular"],
    "hip":            ["hip", "acetabular", "femoral head", "iliopsoas", "ischiofe", "greater trochanter"],
    "elbow":          ["elbow", "epicondyl", "olecranon", "cubital", "lateral humeral"],
    "ankle":          ["ankle", "achilles", "calcaneal", "achillis", "talofib", "peroneal tendon", "subtalar"],
    "wrist":          ["wrist", "carpal", "carpus", "scaphoid", "distal radius", "radioulnar", "distal ulna"],
    "lumbar spine":   ["lumbar", "lower back", "low back", " l1 ", " l2 ", " l3 ", " l4 ", " l5 ", "lumb", "lumbosacral"],
    "thoracic spine": ["thoracic", " t1 ", " t2 ", " t3 ", " t4 ", " t5 "],
    "cervical spine": ["cervical", " c3 ", " c4 ", " c5 ", " c6 ", " c7 ", "cerv"],
}


# ── joint fetching ─────────────────────────────────────────────────────────

def _fetch_joint(catalog_term: str, meta: dict) -> dict:
    code = meta["code"]
    print(f"  → fetching joint: {catalog_term} ({code})")
    concept = _get(f"{BASE}/{code}", include="full")
    children = _get(f"{BASE}/{code}/children") or []
    return {
        "catalog_term": catalog_term,
        "snomed_code": code,
        "snomed_name": concept.get("name", ""),
        "skos_relation": meta["skos"],
        "children": [
            {"snomed_code": c["code"], "snomed_name": c["name"]}
            for c in (children if isinstance(children, list) else [])
        ],
    }


# ── injury target derivation from seed.py ─────────────────────────────────

def _injury_targets() -> list[dict]:
    """
    Read PERSONAS from seed.py, deduplicate on (affected_joints[0], snomedct_hint),
    and return the 19 unique resolver inputs.
    """
    from app.knowledge_graph.seed import PERSONAS

    seen: set[tuple[str, str]] = set()
    targets: list[dict] = []
    for persona in PERSONAS:
        for inj in persona.get("injuries", []):
            hint: str | None = inj.get("snomedct_hint")
            joints: list[str] = inj.get("affected_joints") or []
            joint = joints[0] if joints else None
            if not hint or not joint:
                continue
            key = (joint, hint)
            if key in seen:
                continue
            seen.add(key)
            targets.append({
                "label": hint,
                "expected_joint": joint,
                "code": CODE_OVERRIDES.get(hint),
            })
    return targets


# ── single injury resolver ─────────────────────────────────────────────────

def _code_maps_to_joint(code: str) -> bool:
    """Return True if code is one of the 9 joints or an ancestor path passes through one."""
    if code in _JOINT_CODES:
        return True
    try:
        paths = _get(f"{BASE}/{code}/pathsToRoot")
        if isinstance(paths, list):
            for path in paths:
                for node in (path if isinstance(path, list) else []):
                    if (node.get("code") or "") in _JOINT_CODES:
                        return True
    except httpx.HTTPStatusError:
        pass
    return False


def _extract_finding_site(concept: dict, expected_joint: str) -> dict | None:
    """Find the body-structure association that maps to one of the 9 catalog joints.

    NCI EVS exposes SNOMED CT role relationships (Has finding site, etc.) as
    `associations` with type 'RO'. Three-pass strategy:
      1. relatedCode is directly one of our 9 joint codes
      2. relatedCode's pathsToRoot passes through a joint code (covers joint sub-structures)
      3. relatedName keyword match against the expected_joint (covers tendons/bursae/bones
         that are anatomically at the joint but not hierarchically under the joint node)
    """
    candidates = [
        a for a in (concept.get("associations") or [])
        if a.get("type") == "RO" and a.get("relatedCode")
    ]
    # Pass 1: direct joint code match
    for a in candidates:
        if a["relatedCode"] in _JOINT_CODES:
            return {"code": a["relatedCode"], "name": a.get("relatedName", ""), "match": "direct"}
    # Pass 2: hierarchical (pathsToRoot through a joint)
    for a in candidates:
        if _code_maps_to_joint(a["relatedCode"]):
            return {"code": a["relatedCode"], "name": a.get("relatedName", ""), "match": "hierarchy"}
    # Pass 3: keyword match on relatedName against expected_joint
    keywords = _JOINT_KEYWORDS.get(expected_joint, [])
    for a in candidates:
        name_lower = (a.get("relatedName") or "").lower()
        if any(kw.strip() in name_lower for kw in keywords):
            return {"code": a["relatedCode"], "name": a.get("relatedName", ""), "match": "keyword"}
    return None


def resolve_injury(entry: dict) -> dict | None:
    label = entry["label"]
    expected_joint = entry["expected_joint"]
    pinned_code: str | None = entry.get("code")

    print(f"  → resolving injury: {label}", end="", flush=True)

    if pinned_code:
        code = pinned_code
    else:
        try:
            data = _get(
                f"{BASE}/search",
                term=label,
                type="contains",
                include="minimal",
                pageSize=1,
            )
            concepts = data.get("concepts") or []
            if not concepts:
                print(f"  ✗ {label}: no search results")
                return None
            code = concepts[0]["code"]
        except httpx.HTTPStatusError as e:
            print(f"  ✗ {label}: search failed ({e})")
            return None

    try:
        concept = _get(f"{BASE}/{code}", include="full")
    except httpx.HTTPStatusError as e:
        print(f"  ✗ {label}: concept fetch failed ({e})")
        return None
    finding_site = _extract_finding_site(concept, expected_joint)
    validated = False
    fs_code = fs_name = None

    if finding_site and finding_site.get("code"):
        fs_code = finding_site["code"]
        fs_name = finding_site["name"]
        validated = True

    match_strategy = finding_site.get("match", "") if finding_site else ""
    mark = "✓" if validated else "✗"
    if pinned_code and validated:
        tag = "[pinned]"
    elif validated:
        tag = f"[{match_strategy}]"
    else:
        tag = "[WARN: finding site not a catalog joint]"
    print(f"\r  {mark} {label:<42} → {code} | fs: {fs_code} ({fs_name}) {tag}")
    print(f"\r  {mark} {label:<42} → {code} | fs: {fs_code} ({fs_name}) {tag}")

    return {
        "label": label,
        "expected_joint": expected_joint,
        "disorder_code": code,
        "disorder_name": concept.get("name", ""),
        "finding_site_code": fs_code,
        "finding_site_name": fs_name,
        "validated": validated,
    }


# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("\n=== SNOMED CT subset builder ===\n")

    # 1. Joints
    print("── joints ────────────────────────────────────────────")
    joints = []
    for catalog_term, meta in JOINT_MAP.items():
        joints.append(_fetch_joint(catalog_term, meta))

    # 2. Injuries
    print("\n── injuries ──────────────────────────────────────────")
    targets = _injury_targets()
    print(f"  {len(targets)} unique targets derived from seed.py PERSONAS\n")

    injuries: list[dict] = []
    warnings = 0
    for entry in targets:
        result = resolve_injury(entry)
        if result is None:
            warnings += 1
            continue
        if not result["validated"]:
            warnings += 1
        injuries.append(result)

    # 3. Write output
    subset = {
        "_note": (
            "Auto-generated by scripts/build_snomed_subset.py. "
            "Do not edit by hand — re-run the script to update."
        ),
        "joints": joints,
        "injuries": injuries,
    }
    OUTPUT_PATH.write_text(json.dumps(subset, indent=2))

    print(f"\n✓ wrote {OUTPUT_PATH}")
    print(f"  joints:   {len(joints)}")
    print(f"  injuries: {len(injuries)}")
    if warnings:
        print(f"  ⚠  {warnings} warning(s) — review ✗ lines above and fix snomedct_hint or add a code override")
    else:
        print("  all injuries validated ✓")


if __name__ == "__main__":
    main()
