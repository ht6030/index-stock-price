import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class FundConfig:
    name: str
    short_name: str
    association_fund_cd: str


@dataclass
class AppConfig:
    funds: list[FundConfig]
    slack_bot_token: str
    slack_channel_id: str
    data_dir: Path


def load_config() -> AppConfig:
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config" / "funds.yml"

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    funds = [FundConfig(**fund) for fund in raw["funds"]]

    return AppConfig(
        funds=funds,
        slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
        slack_channel_id=os.environ["SLACK_CHANNEL_ID"],
        data_dir=project_root / "data",
    )
