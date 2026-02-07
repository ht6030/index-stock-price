from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

API_BASE = "https://developer.am.mufg.jp"


@dataclass
class FundPrice:
    fund_name: str
    date: date
    nav: int
    daily_change: int
    daily_change_pct: float
    pct_change_1m: str
    pct_change_1y: str


def _extract_datasets(data: dict) -> list[dict]:
    """APIレスポンスからdatasetsリストを取得する。"""
    return data.get("datasets", [])


def fetch_latest(association_fund_cd: str) -> dict:
    """MUFG APIから最新ファンド情報を取得する。"""
    url = f"{API_BASE}/fund_information_latest/association_fund_cd/{association_fund_cd}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    items = _extract_datasets(resp.json())
    if not items:
        raise ValueError(f"No data returned for fund {association_fund_cd}")
    return items[0]


def fetch_by_date(association_fund_cd: str, base_date: str) -> dict | None:
    """MUFG APIから特定日のファンド情報を取得する。データなしの場合はNoneを返す。"""
    url = (
        f"{API_BASE}/fund_information_date"
        f"/association_fund_cd/{association_fund_cd}"
        f"/base_date/{base_date}"
    )
    resp = requests.get(url, timeout=30)
    if resp.status_code in (400, 404):
        return None
    resp.raise_for_status()
    items = _extract_datasets(resp.json())
    if not items or items[0].get("nav") is None:
        return None
    return items[0]


def parse_fund_price(raw: dict, fund_name: str) -> FundPrice:
    """APIレスポンスからFundPriceオブジェクトを構築する。"""
    base_date_str = str(raw["base_date"])
    d = date(int(base_date_str[:4]), int(base_date_str[4:6]), int(base_date_str[6:8]))

    cmp = raw.get("cmp_prev_day", "0")
    daily_change = int(cmp) if cmp and cmp != "-" else 0

    pct = raw.get("percentage_change", "0")
    daily_change_pct = float(pct) if pct and pct != "-" else 0.0

    return FundPrice(
        fund_name=fund_name,
        date=d,
        nav=int(raw["nav"]),
        daily_change=daily_change,
        daily_change_pct=daily_change_pct,
        pct_change_1m=raw.get("percentage_change_1m", "-"),
        pct_change_1y=raw.get("percentage_change_1y", "-"),
    )


def load_history(path: Path) -> list[dict]:
    """JSONヒストリファイルを読み込む。ファイルがなければ空リストを返す。"""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(path: Path, history: list[dict]) -> None:
    """JSONヒストリファイルを保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def append_to_history(path: Path, base_date: str, nav: int) -> list[dict]:
    """ヒストリに新しいデータポイントを追記する。重複は追加しない。"""
    history = load_history(path)
    existing_dates = {entry["date"] for entry in history}
    if base_date not in existing_dates:
        history.append({"date": base_date, "nav": nav})
        history.sort(key=lambda x: x["date"])
        save_history(path, history)
    return history
