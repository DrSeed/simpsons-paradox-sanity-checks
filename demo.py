# Self-contained demo: simulate data with a hidden confounder and flag the paradox.
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sanity_checks import detect_simpsons_paradox, screen_confounder


def main():
    os.makedirs("figures", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    rng = np.random.default_rng(42)

    # Each group has a negative within-group trend, but higher groups sit higher,
    # producing a positive overall trend: the classic Simpson's paradox.
    frames = []
    for i, shift in enumerate([0, 6, 12]):
        x = rng.normal(shift, 1.2, 50)
        y = -0.9 * x + shift * 2.0 + rng.normal(0, 0.6, 50)
        frames.append(pd.DataFrame({"x": x, "y": y, "group": "batch_" + str(i)}))
    df = pd.concat(frames, ignore_index=True)

    overall, per_group, flag = detect_simpsons_paradox(df, "x", "y", "group")
    eta = screen_confounder(df, "x", "group")

    # Save a summary table.
    summary = per_group.copy()
    summary["overall_corr"] = round(overall, 3)
    summary["paradox_detected"] = flag
    summary["confounder_eta_sq"] = round(eta, 3)
    summary.to_csv("results/summary.csv", index=False)

    # Plot overall fit vs per-group fits.
    fig, ax = plt.subplots(figsize=(7, 5))
    colours = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for (g, sub), c in zip(df.groupby("group"), colours):
        ax.scatter(sub["x"], sub["y"], s=18, alpha=0.7, color=c, label=g)
        coef = np.polyfit(sub["x"], sub["y"], 1)
        xs = np.linspace(sub["x"].min(), sub["x"].max(), 20)
        ax.plot(xs, coef[0] * xs + coef[1], color=c, lw=2)

    coef_all = np.polyfit(df["x"], df["y"], 1)
    xs_all = np.linspace(df["x"].min(), df["x"].max(), 50)
    ax.plot(xs_all, coef_all[0] * xs_all + coef_all[1], color="black", lw=3,
            ls="--", label="overall trend")

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Simpson's paradox: overall vs within-group trends")
    ax.legend()
    fig.tight_layout()
    fig.savefig("figures/demo.png", dpi=120)

    print("Overall correlation:", round(overall, 3))
    print("Paradox detected:", flag)
    print("Wrote figures/demo.png and results/summary.csv")


if __name__ == "__main__":
    main()
