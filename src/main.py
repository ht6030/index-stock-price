import sys

from config import load_config
from fund_data import fetch_latest, parse_fund_price, append_to_history, load_history
from backfill import backfill
from chart import generate_charts
from slack_notifier import SlackNotifier


def main() -> None:
    config = load_config()
    notifier = SlackNotifier(config.slack_bot_token, config.slack_channel_id)

    for fund in config.funds:
        print(f"Processing: {fund.name}")
        try:
            history_path = config.data_dir / f"{fund.association_fund_cd}_history.json"

            # 初回: バックフィル
            history = load_history(history_path)
            if len(history) < 5:
                print("  History is empty or insufficient, running backfill...")
                history = backfill(fund.association_fund_cd, config.data_dir)

            # 最新データ取得
            raw = fetch_latest(fund.association_fund_cd)
            price = parse_fund_price(raw, fund.name)
            print(f"  Latest: {price.nav:,} yen ({price.date})")

            # ヒストリに追記
            base_date = str(raw["base_date"])
            history = append_to_history(history_path, base_date, price.nav)

            # チャート生成
            chart_dir = f"/tmp/charts/{fund.association_fund_cd}"
            chart_paths = generate_charts(fund.short_name, history, chart_dir)
            print(f"  Generated {len(chart_paths)} charts")

            # Slack通知
            notifier.notify(price, chart_paths)
            print(f"  Slack notification sent")

        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            continue

    print("Done.")


if __name__ == "__main__":
    main()
