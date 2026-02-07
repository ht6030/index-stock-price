import time
from datetime import date, timedelta
from pathlib import Path

from fund_data import fetch_by_date, load_history, save_history

BACKFILL_DAYS = 400
REQUEST_INTERVAL = 0.5


def generate_weekday_dates(end_date: date, days_back: int) -> list[str]:
    """end_dateからdays_back日前まで、土日を除いた日付リストを返す。"""
    start_date = end_date - timedelta(days=days_back)
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 月〜金
            dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return dates


def backfill(association_fund_cd: str, data_dir: Path) -> list[dict]:
    """過去データをAPIから一括取得してヒストリファイルに保存する。"""
    history_path = data_dir / f"{association_fund_cd}_history.json"
    history = load_history(history_path)
    existing_dates = {entry["date"] for entry in history}

    today = date.today()
    target_dates = generate_weekday_dates(today, BACKFILL_DAYS)
    dates_to_fetch = [d for d in target_dates if d not in existing_dates]

    if not dates_to_fetch:
        print(f"  Backfill: no new dates to fetch for {association_fund_cd}")
        return history

    print(f"  Backfill: fetching {len(dates_to_fetch)} dates for {association_fund_cd}...")
    fetched = 0
    skipped = 0

    for i, dt in enumerate(dates_to_fetch):
        try:
            raw = fetch_by_date(association_fund_cd, dt)
            if raw and raw.get("nav") is not None:
                history.append({"date": str(raw["base_date"]), "nav": int(raw["nav"])})
                fetched += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"    Error fetching {dt}: {e}")
            skipped += 1

        if i < len(dates_to_fetch) - 1:
            time.sleep(REQUEST_INTERVAL)

        if (i + 1) % 50 == 0:
            print(f"    Progress: {i + 1}/{len(dates_to_fetch)} (fetched={fetched}, skipped={skipped})")

    # 日付順にソートして保存
    history.sort(key=lambda x: x["date"])
    # 重複除去
    seen = set()
    unique_history = []
    for entry in history:
        if entry["date"] not in seen:
            seen.add(entry["date"])
            unique_history.append(entry)

    save_history(history_path, unique_history)
    print(f"  Backfill complete: {fetched} fetched, {skipped} skipped, {len(unique_history)} total records")
    return unique_history
