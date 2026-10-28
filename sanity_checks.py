# Sanity-check helpers that catch common analysis mistakes before you trust them.
import numpy as np
import pandas as pd


def pearson(x, y):
    # Simple Pearson correlation without extra dependencies.
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.std() == 0 or y.std() == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def detect_simpsons_paradox(df, x, y, group):
    # Returns overall correlation and per-group correlations, and flags a reversal.
    overall = pearson(df[x], df[y])
    rows = []
    for g, sub in df.groupby(group):
        rows.append({"group": g, "n": len(sub), "corr": pearson(sub[x], sub[y])})
    per_group = pd.DataFrame(rows)
    group_signs = np.sign(per_group["corr"].values)
    consistent = len(set(group_signs[group_signs != 0])) <= 1
    reversed_flag = bool(
        consistent
        and len(group_signs[group_signs != 0]) > 0
        and np.sign(overall) != group_signs[group_signs != 0][0]
    )
    return overall, per_group, reversed_flag


def screen_confounder(df, feature, batch):
    # Measures how strongly a feature tracks a categorical batch using group means.
    grand_mean = df[feature].mean()
    ss_total = float(((df[feature] - grand_mean) ** 2).sum())
    ss_between = 0.0
    for _, sub in df.groupby(batch):
        ss_between += len(sub) * (sub[feature].mean() - grand_mean) ** 2
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    return float(eta_sq)


def zscore_check(matrix, axis):
    # Z-scores a matrix along the given axis; axis=1 is per-row (per-gene).
    arr = np.asarray(matrix, dtype=float)
    if axis == 1:
        mean = arr.mean(axis=1, keepdims=True)
        std = arr.std(axis=1, keepdims=True)
    else:
        mean = arr.mean(axis=0, keepdims=True)
        std = arr.std(axis=0, keepdims=True)
    std[std == 0] = 1.0
    return (arr - mean) / std


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    # Build a toy dataset where the within-group trend reverses the overall trend.
    frames = []
    for i, shift in enumerate([0, 5, 10]):
        x = rng.normal(shift, 1.0, 40)
        y = -0.8 * x + shift * 1.5 + rng.normal(0, 0.5, 40)
        frames.append(pd.DataFrame({"x": x, "y": y, "group": f"g{i}"}))
    df = pd.concat(frames, ignore_index=True)

    overall, per_group, flag = detect_simpsons_paradox(df, "x", "y", "group")
    print("Overall correlation:", round(overall, 3))
    print(per_group)
    print("Simpson's paradox detected:", flag)

    eta = screen_confounder(df, "x", "group")
    print("Confounding (eta squared) of x with group:", round(eta, 3))
