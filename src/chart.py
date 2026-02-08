import platform
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


def setup_font():
    """OSに応じて日本語フォントを設定する。"""
    system = platform.system()
    if system == "Darwin":
        font_candidates = ["Hiragino Sans", "Hiragino Kaku Gothic Pro"]
    else:
        font_candidates = ["Noto Sans CJK JP", "Noto Sans CJK"]

    matplotlib.rcParams["font.family"] = font_candidates + ["sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False


def generate_charts(
    fund_short_name: str,
    history: list[dict],
    output_dir: str = "/tmp/charts",
) -> list[str]:
    """1週間・1ヶ月・1年のチャートPNGを生成し、ファイルパスのリストを返す。"""
    setup_font()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ヒストリを (datetime, nav) のリストに変換
    points = []
    for entry in history:
        dt_str = str(entry["date"])
        dt = datetime(int(dt_str[:4]), int(dt_str[4:6]), int(dt_str[6:8]))
        points.append((dt, entry["nav"]))
    points.sort(key=lambda x: x[0])

    if not points:
        return []

    latest_date = points[-1][0]

    # 1週間チャートのみ生成（データ蓄積を最小限にするため）
    periods = [
        ("1week", "1週間", timedelta(days=7)),
    ]

    chart_paths = []

    for period_key, period_label, delta in periods:
        start_date = latest_date - delta
        period_points = [(dt, nav) for dt, nav in points if dt >= start_date]

        if len(period_points) < 2:
            continue

        dates = [p[0] for p in period_points]
        navs = [p[1] for p in period_points]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dates, navs, color="#2563eb", linewidth=1.8)

        # Y軸をデータ範囲に合わせる (0始まりにしない)
        nav_min, nav_max = min(navs), max(navs)
        margin = max((nav_max - nav_min) * 0.1, 10)
        y_bottom = nav_min - margin
        ax.set_ylim(bottom=y_bottom)
        ax.fill_between(dates, navs, y_bottom, alpha=0.08, color="#2563eb")

        ax.set_title(
            f"{fund_short_name} - {period_label}",
            fontsize=14,
            fontweight="bold",
            pad=12,
        )
        ax.set_ylabel("基準価額 (円)", fontsize=11)

        # X軸フォーマット
        if delta <= timedelta(days=7):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        elif delta <= timedelta(days=31):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m"))

        # Y軸カンマ区切り
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

        ax.grid(True, alpha=0.3, linestyle="--")
        fig.autofmt_xdate()
        plt.tight_layout()

        filepath = f"{output_dir}/{period_key}.png"
        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        chart_paths.append(filepath)

    return chart_paths
