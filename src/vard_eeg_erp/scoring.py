"""Experimental VARS scoring from explicitly configured, manually supplied features."""

import math

DOMAINS = [
    ("V1", "Visual Detection"),
    ("V2", "Aesthetic Attention"),
    ("V3", "Cognitive Evaluation"),
    ("V4", "Sustained Aesthetic Processing"),
    ("V5", "Spatial Engagement"),
    ("V6", "Temporal Persistence"),
]


def score(model, raw):
    if not model.get("version", "").strip() or not model.get("reference", "").strip():
        raise ValueError("Isi versi model dan sumber data acuan normalisasi.")
    if model.get("normalization") != "minmax":
        raise ValueError("Tahap ini mendukung normalisasi Min–Max.")
    codes = {code for code, _ in DOMAINS}
    if set(model["domains"]) != codes or set(raw) != codes:
        raise ValueError("Konfigurasi dan fitur harus mencakup V1–V6.")
    scores = {}
    weights = []
    for code, _ in DOMAINS:
        config = model["domains"][code]
        if not config["definition"].strip() or not config["unit"].strip():
            raise ValueError(f"{code}: isi definisi fitur/ROI/window dan satuan.")
        low, high, weight, value = (
            float(config["minimum"]),
            float(config["maximum"]),
            float(config["weight"]),
            float(raw[code]),
        )
        if not all(math.isfinite(v) for v in (low, high, weight, value)):
            raise ValueError(f"{code}: nilai harus finite.")
        if high <= low or weight < 0 or weight > 1:
            raise ValueError(f"{code}: maksimum harus > minimum dan bobot dalam 0–1.")
        if config["direction"] not in ("higher", "lower"):
            raise ValueError(f"{code}: arah skor tidak dikenal.")
        normalized = min(1.0, max(0.0, (value - low) / (high - low)))
        if config["direction"] == "lower":
            normalized = 1 - normalized
        scores[code] = {
            "raw": value,
            "score": normalized * 100,
            "weight": weight,
            "outside_reference": value < low or value > high,
        }
        weights.append(weight)
    if not math.isclose(sum(weights), 1, abs_tol=1e-6, rel_tol=0):
        raise ValueError("Jumlah bobot V1–V6 harus 1.")
    return {
        "experimental": True,
        "feature_source": "manual",
        "model": model,
        "domains": scores,
        "composite": sum(item["score"] * item["weight"] for item in scores.values()),
    }
