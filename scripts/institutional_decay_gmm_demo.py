"""One-step difference-GMM simulation (synthetic data ONLY).

Real OECD trust observations in this repo have only 2023 and 2025 country
estimates, so Arellano–Bond is not estimable. This toy model demonstrates
the moment equations but reports NO confidence intervals, serial-correlation
tests, Hansen tests or real-world causal evidence. Python stdlib only.
"""
import argparse
import json
import random
from pathlib import Path


def linear_solve(a, b):
    m = [list(row) + [float(v)] for row, v in zip(a, b)]
    n = len(b)
    for k in range(n):
        p = max(range(k, n), key=lambda i: abs(m[i][k]))
        m[k], m[p] = m[p], m[k]
        if abs(m[k][k]) < 1e-10:
            raise ValueError("Singular instruments")
        v = m[k][k]
        m[k] = [q / v for q in m[k]]
        for j in range(n):
            if j != k:
                v = m[j][k]
                m[j] = [u - v * q for u, q in zip(m[j], m[k])]
    return [row[-1] for row in m]


def simulate(n=1400, tmax=9, seed=20261029, rho=0.6, beta=0.45):
    if n < 50 or tmax < 5:
        raise ValueError("Need many independent units and five or more periods")
    rng = random.Random(seed)
    ztz = [[0.] * 3 for _ in range(3)]
    ztx = [[0.] * 2 for _ in range(3)]
    zty = [0.] * 3
    for _ in range(n):
        alpha = rng.gauss(0, 1)
        x = [rng.gauss(0, 1) for _ in range(tmax)]
        y = [alpha / (1 - rho) + rng.gauss(0, .7)]
        for t in range(1, tmax):
            y.append(rho * y[-1] + beta * x[t] + alpha + rng.gauss(0, .7))
        for t in range(3, tmax):
            lhs = [y[t-1]-y[t-2], x[t]-x[t-1]]
            dy = y[t]-y[t-1]
            z = [y[t-2], y[t-3], lhs[1]]
            for j in range(3):
                zty[j] += z[j]*dy
                for k in range(3):
                    ztz[j][k] += z[j]*z[k]
                for k in range(2):
                    ztx[j][k] += z[j]*lhs[k]
    weighted_x = [linear_solve(ztz, [ztx[j][k] for j in range(3)])
                  for k in range(2)]
    weighted_y = linear_solve(ztz, zty)
    a = [[sum(ztx[j][i]*weighted_x[k][j] for j in range(3))
          for k in range(2)] for i in range(2)]
    b = [sum(ztx[j][i]*weighted_y[j] for j in range(3))
         for i in range(2)]
    estimates = linear_solve(a, b)
    return {"status":"synthetic_math_demo_not_empirical_result",
            "true_rho":rho,"estimated_rho":estimates[0],
            "true_beta":beta,"estimated_beta":estimates[1],
            "countries":n,"periods":tmax,"instruments":3,
            "disclaimer":"One-step GMM educational demonstration; no inference or instrument diagnostics."}


def check_real():
    path = Path(__file__).resolve().parents[1] / "data/institutional-decay/trust-country-waves-2023-2025.json"
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    paired = sum(r["group"] == "oecd_member" and r["nationalGovernment2023"] is not None
                 and r["nationalGovernment2025"] is not None for r in rows)
    return {"status":"not_estimable","paired_countries":paired,
            "survey_waves":[2023,2025],"arellano_bond_identified":False,
            "reason":"No lagged differenced outcome from two observed waves; imputation forbidden."}


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--simulate", action="store_true")
    p.add_argument("--countries", type=int, default=1400)
    p.add_argument("--periods", type=int, default=9)
    a=p.parse_args()
    print(json.dumps(simulate(a.countries,a.periods) if a.simulate else check_real(),indent=2))
