"""Frozen-family, paired lineage analysis with explicit missing-assignment bounds."""

import math
import random
from statistics import mean, stdev

from mcbench.records import EvaluationResult
from mcbench.storage import digest, require


def quantile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def paired_report(assignments: dict, weights: dict, results: list[EvaluationResult], *,
                  protocol_id: str, checkpoint_id: str, seed=0, replicates=10000,
                  invalidating_flags: set[str] | None = None):
    """assignments: lineage -> family -> registered pair IDs at one endpoint.

    Every assigned lineage stays in the denominator for attrition bounds. A
    lineage with any missing family/instance/arm has no complete paired estimate.
    Bootstrap units are entire independent lineages, never teammates/probes.
    """
    require(assignments and weights and all(math.isfinite(w) and w > 0 for w in weights.values()),
            "ANALYSIS_PLAN")
    require(type(replicates) is int and replicates >= 1, "ANALYSIS_PLAN")
    invalidating_flags = (invalidating_flags if invalidating_flags is not None else {
        "contaminated", "invalid_setup", "state_loss", "drift_quarantined", "infrastructure_interruption"})
    maximum = max(weights.values())
    scaled = {k: v / maximum for k, v in weights.items()}
    weights = {k: v / sum(scaled.values()) for k, v in scaled.items()}
    require(all(w > 0 for w in weights.values()), "ANALYSIS_WEIGHT_RANGE")
    pair_owners = {}
    for lineage, families in assignments.items():
        require(set(families) == set(weights), "INCOMPLETE_ASSIGNMENT")
        for family, pairs in families.items():
            require(pairs, "INCOMPLETE_ASSIGNMENT")
            for pair in pairs:
                require(pair not in pair_owners, "DUPLICATE_PAIR_ASSIGNMENT")
                pair_owners[pair] = (lineage, family)
    observed, ids = {}, {}
    for result in results:
        require(result.protocol_id == protocol_id and result.checkpoint_id == checkpoint_id,
                "ENDPOINT_MISMATCH")
        require(result.pair_id in pair_owners and
                pair_owners[result.pair_id][0] == result.lineage_id, "UNASSIGNED_RESULT")
        payload = digest(result.model_dump())
        if result.result_id in ids:
            require(ids[result.result_id] == payload, "IDEMPOTENCY_CONFLICT")
            continue
        ids[result.result_id] = payload
        key = (result.pair_id, result.arm)
        require(key not in observed, "DUPLICATE_ARM_RESULT")
        observed[key] = result
    raw, incomplete = [], []
    for lineage, families in sorted(assignments.items()):
        qs = {"experienced": 0.0, "initial": 0.0}
        family_scores, missing = {}, False
        for family, pairs in families.items():
            ys = {"experienced": [], "initial": []}
            for pair in pairs:
                arms = [observed.get((pair, arm)) for arm in qs]
                if all(arms):
                    require(arms[0].instance_id == arms[1].instance_id, "UNMATCHED_INSTANCE")
                for arm, result in zip(qs, arms):
                    if (result is None or result.outcome in {"censored", "invalid"}
                            or result.success is None or set(result.validity_flags) & invalidating_flags):
                        missing = True
                    else:
                        ys[arm].append(int(result.success))
            family_scores[family] = {arm: mean(y) if len(y) == len(pairs) else None
                                      for arm, y in ys.items()}
            for arm in qs:
                value = family_scores[family][arm]
                if value is not None:
                    qs[arm] += weights[family] * value
        if missing:
            incomplete.append(lineage)
        else:
            raw.append({"lineage": lineage, **qs, "gain": qs["experienced"] - qs["initial"],
                        "families": family_scores})
    gains = [r["gain"] for r in raw]
    interval = None
    if gains:
        rng = random.Random(seed)
        samples = [mean(rng.choices(gains, k=len(gains))) for _ in range(replicates)]
        interval = [quantile(samples, .025), quantile(samples, .975)]
    missing_count, assigned = len(incomplete), len(assignments)
    return {"schema": "strata/PairedReport/1", "protocol_id": protocol_id,
            "checkpoint_id": checkpoint_id, "assigned_lineages": assigned,
            "complete_lineages": len(raw), "missing_lineages": incomplete, "raw_pairs": raw,
            "experienced": mean(r["experienced"] for r in raw) if raw else None,
            "initial": mean(r["initial"] for r in raw) if raw else None,
            "gain": mean(gains) if gains else None, "percentile_95_ci": interval,
            "attrition_bounds": [(sum(gains) - missing_count) / assigned,
                                  (sum(gains) + missing_count) / assigned],
            "bootstrap_seed": seed, "bootstrap_replicates": replicates,
            "independent_unit": "lineage", "confirmatory_claim": False,
            "validity_flags": sorted({flag for result in results for flag in result.validity_flags}),
            "invalidating_flags": sorted(invalidating_flags),
            "qualification": "Requires registered sample, missingness, identity and integrity gates"}


def common_support_area(series: dict[str, dict[int, float]]):
    """Normalized trapezoids on common observed times only; no endpoint fabrication."""
    require(series, "ANALYSIS_PLAN")
    times = sorted(set.intersection(*(set(v) for v in series.values())))
    if len(times) < 2:
        return {"times": times, "areas": {key: None for key in series}}
    require(all(type(t) is int and t >= 0 for t in times), "ANALYSIS_PLAN")
    require(all(math.isfinite(values[t]) for values in series.values() for t in times),
            "ANALYSIS_PLAN")
    return {"times": times, "areas": {key: sum((values[a] + values[b]) * (b - a) / 2
            for a, b in zip(times, times[1:])) / (times[-1] - times[0])
            for key, values in series.items()}}


def holm(p_values: dict[str, float]):
    require(all(math.isfinite(p) and 0 <= p <= 1 for p in p_values.values()), "ANALYSIS_PLAN")
    result, previous = {}, 0.0
    for i, (name, p) in enumerate(sorted(p_values.items(), key=lambda pair: pair[1])):
        previous = max(previous, min(1.0, (len(p_values) - i) * p))
        result[name] = previous
    return result


def plan_sample(pilot_gains, delta=.1, attrition=.1):
    require(len(pilot_gains) >= 2 and 0 < delta <= 1 and 0 <= attrition < 1
            and all(math.isfinite(x) and -1 <= x <= 1 for x in pilot_gains), "ANALYSIS_PLAN")
    count = math.ceil(((1.96 + .84) * stdev(pilot_gains) / delta) ** 2)
    return {"normal_approximation": count, "admit_with_attrition": math.ceil(count / (1 - attrition)),
            "simulation_required": True, "confirmatory_sample_approved": False}
