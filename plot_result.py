import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import json
import re
from datetime import datetime

def format_timestamp(row):
    try:
        dt = datetime.strptime(str(row["date"]), "%Y-%m-%d")
        date_str = dt.strftime("%b %d")
        return f"{date_str}\n{row['time']}"
    except Exception:
        return f"{row['date']}\n{row['time']}"

def format_duration(seconds):
    if seconds >= 60:
        minutes = seconds / 60
        return f"{minutes:.1f} min"
    return f"{seconds:.1f} s"

def generate_chart():
    config_path = os.environ.get("INPUT")
    if not config_path or not os.path.exists(config_path):
        json_files = glob.glob("*.json")
        configs = []
        for jf in json_files:
            try:
                with open(jf, "r") as f:
                    data = json.load(f)
                    if "tests" in data and "testName" in data:
                        configs.append(jf)
            except Exception:
                pass
        if configs:
            config_path = sorted(configs)[0]
    pc_specs = {}
    data_specs = {}
    report_file = ""
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            report_file = config.get("reportFile", "")
            if report_file and os.path.exists(report_file):
                with open(report_file, "r") as rf:
                    report = json.load(rf)
                    pc_specs = report.get("pcSpecs", {})
                    data_specs = report.get("dataSpecs", {})
            else:
                pc_specs = config.get("pcSpecs", {})
                data_specs = config.get("dataSpecs", {})
        except Exception as e:
            print(f"Error loading config file: {config_path}: {e}")

    KNOWN_PHASES = ["train", "match"]
    series = {}
    report_dir = os.path.dirname(report_file) if report_file else ""
    csv_pattern = os.path.join(report_dir, "*_report.csv") if report_dir else "*_report.csv"
    for file_path in sorted(glob.glob(csv_pattern)):
        basename = os.path.basename(file_path).replace("_report.csv", "")
        phase = next((p for p in KNOWN_PHASES if basename == p or basename.endswith(f"_{p}")), None)
        if phase is None:
            continue
        dataset = basename[: -(len(phase) + 1)] if basename != phase else "default"
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            continue
        if not df.empty:
            df["timestamp"] = df.apply(format_timestamp, axis=1)
            series[(dataset, phase)] = df

    if not series:
        print("No report data found.")
        return

    all_datasets = sorted(set(d for d, _ in series.keys()))
    total_runs = max(len(df) for df in series.values())

    def concat_phase(phase_name):
        frames = [df for (d, p), df in series.items() if p == phase_name]
        return pd.concat(frames, ignore_index=True) if frames else None

    train_all = concat_phase("train")
    match_all = concat_phase("match")

    avg_train_sec = (train_all["duration"].mean() * 60) if train_all is not None else 0.0
    best_train_sec = (train_all["duration"].min() * 60) if train_all is not None else 0.0
    avg_match_sec = (match_all["duration"].mean() * 60) if match_all is not None else 0.0
    best_match_sec = (match_all["duration"].min() * 60) if match_all is not None else 0.0
    ratio = (avg_train_sec / avg_match_sec) if avg_match_sec > 0 else 0.0
    plt.rcParams['font.family'] = 'sans-serif'
    fig = plt.figure(figsize=(11, 7.5), facecolor='#0b0b12')
    gs = fig.add_gridspec(2, 1, height_ratios=[5, 2], hspace=0.3)
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor('#10111d')

    
    PHASE_COLORS = {"train": "#a855f7", "match": "#f97316"}
    PHASE_ANNOT  = {"train": (8, '#d8b4fe', 'semibold'), "match": (-12, '#ffedd5', 'normal')}
    DATASET_LINESTYLES = ["-", "--", "-."]
    DATASET_MARKERS    = ["o", "^",  "s"]

    dataset_idx = {d: i for i, d in enumerate(all_datasets)}

    
    for (dataset, phase), df in sorted(series.items()):
        color     = PHASE_COLORS.get(phase, "#06b6d4")
        idx       = dataset_idx[dataset]
        linestyle = DATASET_LINESTYLES[idx % len(DATASET_LINESTYLES)]
        marker    = DATASET_MARKERS[idx % len(DATASET_MARKERS)]
        label     = phase.capitalize() if len(all_datasets) == 1 else f"{dataset} {phase}"

        x_vals = df["timestamp"]
        y_vals = df["duration"]

        ax.plot(x_vals, y_vals, color=color, linestyle=linestyle, linewidth=2,
                marker=marker, markersize=6, label=f"{label} (min)")
        ax.fill_between(x_vals, y_vals, color=color, alpha=0.08)

        offset, annot_color, weight = PHASE_ANNOT.get(phase, (8, '#ffffff', 'normal'))
        for x_coord, y_coord in zip(x_vals, y_vals):
            ax.annotate(f"{y_coord * 60:.0f}s", (x_coord, y_coord),
                        textcoords="offset points", xytext=(0, offset),
                        ha='center', color=annot_color, fontsize=8, fontweight=weight)

    
    ax.set_title("Zingg Performance History", color='#ffffff', fontsize=13, pad=15, fontweight='bold')
    ax.set_ylabel("Duration (minutes)", color='#8e8f9e', fontsize=9.5)
    ax.set_xlabel("Execution Time", color='#8e8f9e', fontsize=9.5)
    
    ax.tick_params(axis='both', colors='#8e8f9e', labelsize=8.5)
    ax.grid(True, color='#222332', linestyle=':', linewidth=0.8)

    max_duration = max(df["duration"].max() for df in series.values())
    ax.set_ylim(0, max_duration * 1.3)

    
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color('#222332')

    
    ax.legend(facecolor='#151625', edgecolor='#222332', labelcolor='#ffffff', loc='upper right', framealpha=0.9)

    
    fig.text(0.06, 0.95, "ZINGG", color='#ffffff', fontsize=15, fontweight='black', alpha=0.95)
    fig.text(0.125, 0.953, "·  Performance Report", color='#a855f7', fontsize=10.5, alpha=0.85)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    fig.text(0.94, 0.953, f"Generated: {today_str}", color='#8e8f9e', fontsize=8.5, ha='right')

    ax_footer = fig.add_subplot(gs[1])
    ax_footer.axis('off')

    ax_footer.text(0.02, 0.85, "PC Specs", color='#ffffff', fontsize=10.5, fontweight='bold')
    pc_keys = ["OS", "CPU", "RAM", "Storage", "Spark", "Java"]
    y_pos = 0.65
    for k in pc_keys:
        val = str(pc_specs.get(k, "N/A"))
        if k == "Java" and "version" in val.lower():
            parts = val.split()
            if len(parts) >= 3:
                val = f"{parts[0]} {parts[2]}"
        elif k == "Spark" and "version" in val.lower():
            match = re.search(r"version\s+([\d\.]+)", val)
            if match:
                val = f"Spark {match.group(1)}"
        
        if len(val) > 25:
            val = val[:22] + "..."
            
        ax_footer.text(0.02, y_pos, f"{k}:", color='#a855f7', fontsize=8.5, fontweight='semibold')
        ax_footer.text(0.11, y_pos, val, color='#cbd5e1', fontsize=8.5)
        y_pos -= 0.12

    ax_footer.text(0.35, 0.85, "Data Specs", color='#ffffff', fontsize=10.5, fontweight='bold')
    data_keys = ["Dataset", "Records", "Fields", "Pairs", "Blocking", "Model"]
    y_pos = 0.65
    for k in data_keys:
        val = str(data_specs.get(k, "N/A"))
        if len(val) > 35:
            val = val[:32] + "..."
            
        ax_footer.text(0.35, y_pos, f"{k}:", color='#f97316', fontsize=8.5, fontweight='semibold')
        ax_footer.text(0.44, y_pos, val, color='#cbd5e1', fontsize=8.5)
        y_pos -= 0.12

    ax_footer.text(0.76, 0.85, "Run Summary", color='#ffffff', fontsize=10.5, fontweight='bold')
    summary_items = [
        ("Total Runs", f"{total_runs}"),
        ("Avg Train", format_duration(avg_train_sec)),
        ("Avg Match", format_duration(avg_match_sec)),
        ("Best Train", format_duration(best_train_sec)),
        ("Best Match", format_duration(best_match_sec)),
        ("Train/Match", f"{ratio:.1f}x" if ratio > 0 else "N/A")
    ]
    y_pos = 0.65
    for label, val in summary_items:
        ax_footer.text(0.76, y_pos, f"{label}:", color='#a855f7', fontsize=8.5, fontweight='semibold')
        ax_footer.text(0.87, y_pos, val, color='#cbd5e1', fontsize=8.5)
        y_pos -= 0.12

    chart_dir = os.path.dirname(report_file) if report_file else ""
    if chart_dir:
        os.makedirs(chart_dir, exist_ok=True)
        chart_path = os.path.join(chart_dir, "performance_chart.png")
    else:
        chart_path = "performance_chart.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Performance chart successfully updated at {chart_path}!")

if __name__ == "__main__":
    generate_chart()