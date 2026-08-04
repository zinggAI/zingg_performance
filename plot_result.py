import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import glob
import json
import re
import subprocess
from datetime import datetime


OSS_REPO = os.environ.get("OSS_REPO", "zinggAI/zingg")


def find_reports_repo(report_file):
    env = os.environ.get("REPORTS_REPO")
    if env and os.path.isdir(env):
        return env
    if report_file:
        # changing separators for enabling any os to use this as \ is used by windows and then splitting
        parts = report_file.replace("\\", "/").split("/")


        if "zingg_community_performance_reports" in parts:
            i = parts.index("zingg_community_performance_reports")
            cand = "/".join(parts[: i + 1]) or "."
            if os.path.isdir(cand):
                return cand
    for c in ["zingg_community_performance_reports", "."]:
        if os.path.isdir(os.path.join(c, "perf_test", "perf_test_report")):
            return c
    return "."


def git(repo, args):
    return subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True).stdout

# get the past records
def report_history(repo, relpath):
    rows = []
    for sha in git(repo, ["log", "--reverse", "--format=%H", "--", relpath]).split():
        try:
            d = json.loads(git(repo, ["show", f"{sha}:{relpath}"]))
            r = d.get("results", {})
            tr, mt = r.get("train"), r.get("match")
            if isinstance(tr, (int, float)) and isinstance(mt, (int, float)):
                rows.append((datetime.strptime(d["date"], "%Y-%m-%d"), tr, mt))
        except Exception:
            pass
    rows.sort()
    return rows


def failure_dates(workflow):
    try:
        out = subprocess.run(
            ["gh", "run", "list", "-R", OSS_REPO, "--workflow", workflow, "-L", "100",
             "--json", "createdAt,conclusion"],
            capture_output=True, text=True, timeout=60).stdout
        runs = json.loads(out or "[]")
        return sorted({datetime.strptime(r["createdAt"][:10], "%Y-%m-%d")
                       for r in runs if r["conclusion"] == "failure"})
    except Exception:
        return []


def load_specs(report_file):
    try:
        with open(report_file) as f:
            rep = json.load(f)
        return rep.get("pcSpecs", {}), rep.get("dataSpecs", {}), rep.get("test", "")
    except Exception:
        return {}, {}, ""

# def format_timestamp(row):
def config_data_specs(repo, dataset):
    cfg = os.path.join(repo, "perf_test", f"perfTestInput_{dataset}.json")
    try:
        with open(cfg) as f:
            return json.load(f).get("dataSpecs", {})
    except Exception:
        return {}


def format_duration(minutes):
    return f"{minutes:.2f} min" if minutes >= 1 else f"{minutes * 60:.1f} s"


def build_chart(dataset, hist, fails, pc, data, outdir):
    dates = [r[0] for r in hist]; train = [r[1] for r in hist]; match = [r[2] for r in hist]
    plt.rcParams["font.family"] = "sans-serif"
    fig = plt.figure(figsize=(11, 7.5), facecolor="#0b0b12")
    gs = fig.add_gridspec(2, 1, height_ratios=[5, 2], hspace=0.35)
    ax = fig.add_subplot(gs[0]); ax.set_facecolor("#10111d")

    ax.plot(dates, train, color="#a855f7", lw=1.6, marker="o", ms=3, label="Train (min)")
    ax.plot(dates, match, color="#f97316", lw=1.6, marker="s", ms=3, label="Match (min)")
    if fails:
        ax.scatter(fails, [0] * len(fails), marker="x", color="#ef4444", s=40, zorder=5,
                   label=f"Failed run ({len(fails)})")

    ax.set_title(f"Zingg OSS — {dataset} performance history", color="#ffffff",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Duration (minutes)", color="#8e8f9e", fontsize=9.5)
    ax.grid(True, color="#222332", ls=":", lw=0.8)
    ax.tick_params(colors="#8e8f9e", labelsize=8.5)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color("#222332")
    ax.legend(facecolor="#151625", edgecolor="#222332", labelcolor="#ffffff",
              loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    axf = fig.add_subplot(gs[1]); axf.axis("off")
    axf.text(0.02, 0.85, "PC Specs", color="#ffffff", fontsize=10.5, fontweight="bold")
    y = 0.62
    for k in ["OS", "CPU", "RAM", "Storage", "Spark", "Java"]:
        axf.text(0.02, y, f"{k}:", color="#a855f7", fontsize=8.5, fontweight="semibold")
        axf.text(0.11, y, str(pc.get(k, "N/A"))[:24], color="#cbd5e1", fontsize=8.5); y -= 0.13
    axf.text(0.35, 0.85, "Data Specs", color="#ffffff", fontsize=10.5, fontweight="bold")
    y = 0.62
    for k in ["Dataset", "Records", "Fields", "Pairs", "Blocking", "Model"]:
        axf.text(0.35, y, f"{k}:", color="#f97316", fontsize=8.5, fontweight="semibold")
        axf.text(0.45, y, str(data.get(k, "N/A"))[:30], color="#cbd5e1", fontsize=8.5); y -= 0.13
    axf.text(0.76, 0.85, "Run Summary", color="#ffffff", fontsize=10.5, fontweight="bold")
    trains = [t for _, t, _ in hist]; matches = [m for _, _, m in hist]
    summ = [("Data points", str(len(hist))),
            ("Failed runs", str(len(fails))),
            ("Avg train", format_duration(sum(trains) / len(trains)) if trains else "N/A"),
            ("Avg match", format_duration(sum(matches) / len(matches)) if matches else "N/A"),
            ("Best match", format_duration(min(matches)) if matches else "N/A"),
            ("Last run", dates[-1].strftime("%Y-%m-%d") if dates else "N/A")]
    y = 0.62
    for k, v in summ:
        axf.text(0.76, y, f"{k}:", color="#a855f7", fontsize=8.5, fontweight="semibold")
        axf.text(0.88, y, v, color="#cbd5e1", fontsize=8.5); y -= 0.13

    fig.text(0.06, 0.955, "ZINGG", color="#ffffff", fontsize=15, fontweight="black", alpha=0.95)
    fig.text(0.125, 0.958, "·  Performance Report", color="#a855f7", fontsize=10.5, alpha=0.85)

    out = os.path.join(outdir, f"performance_chart_{dataset}.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    return out


def generate_chart():
    config_path = os.environ.get("INPUT")
    report_file = ""
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                report_file = json.load(f).get("reportFile", "")
        except Exception:
            pass

    repo = find_reports_repo(report_file)
    rep_dir_rel = os.path.join("perf_test", "perf_test_report")
    report_files = sorted(glob.glob(os.path.join(repo, rep_dir_rel, "testReport_*.json")))
    if not report_files:
        print(f"No report files under {repo}/{rep_dir_rel}")
        return

    outdir = os.environ.get("CHART_DIR", os.path.join(repo, rep_dir_rel))
    os.makedirs(outdir, exist_ok=True)
    print(f"reports repo: {repo}")
    for rf in report_files:
        name = os.path.basename(rf)[len("testReport_"):-len(".json")]
        relpath = os.path.relpath(rf, repo)
        hist = report_history(repo, relpath)
        if not hist:
            print(f"  {name}: no history, skipping")
            continue
        fails = failure_dates(f"perfTest-{name}.yml")
        pc, data_report, test_name = load_specs(rf)
        data = dict(config_data_specs(repo, name))       # config dataSpecs as base
        data.update(data_report)                         # report values override
        data.setdefault("Dataset", test_name or name)    # we always know the dataset name
        out = build_chart(name, hist, fails, pc, data, outdir)
        print(f"  {name}: {len(hist)} points, {len(fails)} failures -> {out}")


if __name__ == "__main__":
    generate_chart()
