"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import re
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    problems = []
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return problems
    for section, keys in (("metrics", ("id",)), ("slices", ("name", "metric"))):
        current = {tuple(entry.get(key) for key in keys): entry for entry in spec.get(section, [])}
        for old in base_spec.get(section, []):
            identity = tuple(old.get(key) for key in keys)
            new = current.get(identity)
            label = f"ratchet {section}:{'/'.join(map(str, identity))}"
            if new is None:
                problems.append(f"{label} removed")
                continue
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"{label} blocking removed")
            old_th = old.get("threshold", {}) if section == "metrics" else old
            new_th = new.get("threshold", {}) if section == "metrics" else new
            for bound in ("min", "max", "max_increase"):
                if bound in old_th:
                    value = new_th.get(bound)
                    if not _finite_number(value) or (value < old_th[bound] if bound == "min" else value > old_th[bound]):
                        problems.append(f"{label} {bound} loosened or removed")
            if old_th.get("no_significant_drop") and not new_th.get("no_significant_drop"):
                problems.append(f"{label} no_significant_drop removed")
            for field in ("kind", "level", "grader"):
                if field in old and new.get(field) != old[field]:
                    problems.append(f"{label} {field} changed")
    for field in ("seeds", "bootstrap", "eval_set", "labels"):
        if field in base_spec and spec.get(field) != base_spec[field]:
            problems.append(f"ratchet {field} changed on the same eval-set version")
    return problems


def _inspect_report(report: dict, spec: dict, name: str) -> tuple[list[str], Counter, dict]:
    problems, pairs, slices = [], Counter(), {}
    if not isinstance(report, dict):
        return [f"{name}: report must be an object"], pairs, slices
    manifest = report.get("manifest") or {}
    if not isinstance(manifest, dict):
        return [f"{name}: invalid manifest"], pairs, slices
    seeds = manifest.get("seeds")
    items = manifest.get("items")
    rows = report.get("rows")
    metrics = report.get("metrics")
    if (not isinstance(items, int) or isinstance(items, bool) or items < 1
            or not isinstance(seeds, list) or not seeds
            or any(not isinstance(s, int) or isinstance(s, bool) for s in seeds)):
        return [f"{name}: invalid manifest items/seeds"], pairs, slices
    if len(set(seeds)) != len(seeds):
        problems.append(f"{name}: duplicate manifest seeds")
    if not manifest.get("eval_set_sha"):
        problems.append(f"{name}: missing eval_set_sha")
    if not isinstance(rows, list) or not rows:
        return [*problems, f"{name}: missing/empty rows"], pairs, slices
    if not isinstance(metrics, dict):
        return [*problems, f"{name}: invalid metrics"], pairs, slices
    if any(not isinstance(row, dict) for row in rows):
        return [*problems, f"{name}: invalid row"], pairs, slices
    if "eval_set_version" in manifest and manifest["eval_set_version"] != spec.get("eval_set_version"):
        problems.append(f"{name}: eval_set_version differs from spec")
    if len(rows) != items * len(seeds):
        problems.append(f"{name}: row count {len(rows)} != {items} items x {len(seeds)} seeds")
    if report.get("evaluator_failures") != []:
        problems.append(f"{name}: evaluator_failures is non-empty or missing")
    graded = [m["id"] for m in spec.get("metrics", []) if m["id"] in GRADERS]
    for mid, value in metrics.items():
        if value is None and mid == "cost_per_success" and not any(r.get("pass_rate") for r in rows):
            continue  # cost/success is undefined when no run succeeds; pass_rate still blocks.
        if not _finite_number(value):
            problems.append(f"{name}: metric {mid} is missing or non-finite")
    for metric in spec.get("metrics", []):
        if metric["id"] not in metrics:
            problems.append(f"{name}: missing spec metric {metric['id']}")
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{name}: invalid row")
            continue
        item, seed = row.get("item_id"), row.get("seed")
        if not isinstance(item, str) or not item or not isinstance(seed, int) or isinstance(seed, bool):
            problems.append(f"{name}: invalid (item_id, seed)")
            continue
        pairs[item, seed] += 1
        if seed not in seeds:
            problems.append(f"{name}: row seed outside manifest")
        tags = row.get("slices", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags) or len(set(tags)) != len(tags):
            problems.append(f"{name}: invalid slice tags for {item}")
        else:
            tag_set = frozenset(tags)
            if item in slices and slices[item] != tag_set:
                problems.append(f"{name}: inconsistent slice tags for {item}")
            slices[item] = tag_set
        for mid in graded:
            value = row.get(mid)
            if not (isinstance(value, bool) or (_finite_number(value) and value in (0, 1))):
                problems.append(f"{name}: missing/invalid row value {mid}")
        if "cost" in row and (not _finite_number(row["cost"]) or row["cost"] < 0):
            problems.append(f"{name}: invalid row cost")
    if any(count != 1 for count in pairs.values()):
        problems.append(f"{name}: duplicate (item_id, seed) rows")
    item_ids = {item for item, _ in pairs}
    if len(item_ids) != items or set(pairs) != {(item, seed) for item in item_ids for seed in seeds}:
        problems.append(f"{name}: item x seed grid is incomplete")
    # Recompute aggregates: editing a green summary cannot conceal red row values.
    if not problems:
        k_values = sorted({int(match[2]) for mid in metrics
                           if (match := re.fullmatch(r"(pass_at|pass_hat)_(\d+)", mid))})
        recomputed = aggregate([{**row, "cost": row.get("cost", 0.0)} for row in rows], graded, k_values)
        for mid, expected in recomputed.items():
            if mid not in metrics:
                continue
            if mid == "cost_per_success" and not all("cost" in row for row in rows):
                problems.append(f"{name}: cost_per_success without row costs")
            elif expected is None:
                if metrics[mid] is not None:
                    problems.append(f"{name}: aggregate {mid} should be undefined")
            elif not math.isclose(metrics[mid], expected, rel_tol=0, abs_tol=1e-9):
                problems.append(f"{name}: aggregate {mid} differs from rows")
    return list(dict.fromkeys(problems)), pairs, slices


def _per_item_metric(report: dict, metric: str, slice_name: str | None = None) -> dict[str, float]:
    derived = re.fullmatch(r"(pass_at|pass_hat)_(\d+)", metric)
    if derived is None:
        return per_item(report, metric, slice_name)
    by_item = {}
    for row in report["rows"]:
        if slice_name is None or slice_name in row.get("slices", []):
            by_item.setdefault(row["item_id"], []).append(row["pass_rate"])
    fn = stats.pass_at_k if derived[1] == "pass_at" else stats.pass_hat_k
    return {item: fn(len(values), sum(values), int(derived[2])) for item, values in by_item.items()}


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    if not isinstance(spec.get("metrics"), list) or not spec["metrics"]:
        return ["spec: metrics must be a non-empty list"]
    for section, keys in (("metrics", ("id",)), ("slices", ("name", "metric"))):
        seen = set()
        for entry in spec.get(section, []):
            if not isinstance(entry, dict) or any(not isinstance(entry.get(key), str) for key in keys):
                return [f"spec: invalid {section} entry"]
            identity = tuple(entry.get(key) for key in keys)
            if None in identity or identity in seen:
                problems.append(f"spec: invalid/duplicate {section} identity")
            seen.add(identity)
            if section == "metrics" and entry["id"] not in GRADERS and entry["id"] not in ("pass_5", "cost_per_success"):
                if re.fullmatch(r"(?:pass_at|pass_hat)_[1-9]\d*", entry["id"]) is None:
                    problems.append(f"spec: unsupported metric {entry['id']}")
            threshold = entry.get("threshold", {}) if section == "metrics" else entry
            for bound in ("min", "max", "max_increase"):
                if bound in threshold and not _finite_number(threshold[bound]):
                    problems.append(f"spec: non-finite {bound}")
    if problems:
        return problems
    pp, pr_pairs, pr_slices = _inspect_report(pr, spec, "PR")
    bp, base_pairs, base_slices = _inspect_report(base, spec, "baseline")
    problems.extend(pp + bp)
    if pr_pairs != base_pairs:
        problems.append("PR (item_id, seed) multiset differs from baseline")
    if pr_slices != base_slices:
        problems.append("PR item slice tags differ from baseline")
    if isinstance(pr, dict) and isinstance(base, dict):
        pm, bm = pr.get("manifest"), base.get("manifest")
        if isinstance(pm, dict) and isinstance(bm, dict) and pm.get("labels_sha") != bm.get("labels_sha"):
            problems.append("PR labels SHA differs from baseline")
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        identity = f"slice:{name}/{metric}"
        left, right = _per_item_metric(pr, metric, name), _per_item_metric(base, metric, name)
        fail, note = False, ""
        if not left or set(left) != set(right):
            fail, value, note = True, None, "missing slice or unpaired items"
        else:
            value = sum(left.values()) / len(left)
            fail = "min" in entry and value < entry["min"]
            if entry.get("no_significant_drop"):
                keys = sorted(left)
                delta, lo, hi = stats.paired_bootstrap([left[k] for k in keys], [right[k] for k in keys],
                                                      n_resamples=bs.get("n_resamples", 1000),
                                                      rng=bs.get("rng", 2027), confidence=bs.get("confidence", 0.95))
                note = f"Δ {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                fail = fail or hi < 0
        if fail and entry.get("blocking"):
            blocked.append(identity)
        lines.append(f"  {identity:<36} {value!s:<8} {note} {'BLOCK' if fail else 'ok'}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = _per_item_metric(pr, mid), _per_item_metric(base, mid)
            keys = sorted(a)
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
