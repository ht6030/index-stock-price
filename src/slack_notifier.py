from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from fund_data import FundPrice


PERIOD_LABELS = ["1週間チャート"]


class SlackNotifier:
    def __init__(self, bot_token: str, channel_id: str):
        self.client = WebClient(token=bot_token)
        self.channel_id = channel_id

    def notify(self, price: FundPrice, chart_paths: list[str], fund_url: str) -> None:
        """基準価額テキストとチャート画像をSlackに投稿する。"""
        self._post_message(price, fund_url)
        self._upload_charts(price.fund_name, chart_paths)

    def _post_message(self, price: FundPrice, fund_url: str) -> None:
        sign = "+" if price.daily_change >= 0 else ""
        trend = ":chart_with_upwards_trend:" if price.daily_change >= 0 else ":chart_with_downwards_trend:"

        pct_1m = price.pct_change_1m if price.pct_change_1m != "-" else "N/A"
        pct_1y = price.pct_change_1y if price.pct_change_1y != "-" else "N/A"

        message = (
            f"<@U0ABQH0L71Q> {trend} *{price.fund_name}*\n"
            f":calendar: {price.date.strftime('%Y/%m/%d')}\n"
            f":moneybag: 基準価額: *{price.nav:,}円*\n"
            f"前日比: *{sign}{price.daily_change:,}円* ({sign}{price.daily_change_pct}%)\n"
            f"1ヶ月: {pct_1m}% | 1年: {pct_1y}%\n"
            f":link: <{fund_url}|詳細・長期チャートを見る>"
        )

        try:
            self.client.chat_postMessage(
                channel=self.channel_id,
                text=message,
                mrkdwn=True,
            )
        except SlackApiError as e:
            print(f"Error posting message: {e.response['error']}")
            raise

    def _upload_charts(self, fund_name: str, chart_paths: list[str]) -> None:
        if not chart_paths:
            # チャートなし（テキスト通知のみモード）
            return

        for path, label in zip(chart_paths, PERIOD_LABELS):
            try:
                self.client.files_upload_v2(
                    channel=self.channel_id,
                    file=path,
                    title=f"{fund_name} - {label}",
                    initial_comment=f"*{label}*",
                )
            except SlackApiError as e:
                print(f"Error uploading chart {label}: {e.response['error']}")
