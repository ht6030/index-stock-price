# index-stock-price

投資信託の基準価額を毎朝自動取得し、チャート付きでSlackに通知するシステム。

## 機能

- 三菱UFJアセットマネジメント公式APIから基準価額を自動取得
- 前日比 (円・%) を表示
- 1週間・1ヶ月・1年のチャートを画像で送信
- GitHub Actionsで毎朝7時 (JST) に自動実行
- `config/funds.yml` でウォッチ対象ファンドを簡単に追加可能

## セットアップ

### 1. Slackアプリの作成

1. https://api.slack.com/apps にアクセス
2. 「Create New App」→「From scratch」を選択
3. アプリ名 (例: `Fund Monitor`) とワークスペースを指定して作成
4. 左メニュー「OAuth & Permissions」→「Bot Token Scopes」に以下を追加:
   - `chat:write`
   - `files:write`
5. ページ上部の「Install to Workspace」をクリック
6. **Bot User OAuth Token** (`xoxb-...`) をコピー

### 2. Slackチャンネルの準備

1. 通知先チャンネルを作成 (例: `#fund-prices`)
2. チャンネル名をクリック → 下部に表示される **チャンネルID** (`C0123456789`) をコピー
3. チャンネル内で `/invite @アプリ名` を入力してBotを招待

### 3. GitHubリポジトリの設定

1. このリポジトリをGitHubにプッシュ
2. Settings → Secrets and variables → Actions で以下を追加:

| Secret名 | 値 |
|---|---|
| `SLACK_BOT_TOKEN` | `xoxb-...` (上記でコピーしたBot Token) |
| `SLACK_CHANNEL_ID` | `C0123456789` (チャンネルID) |

### 4. 動作確認

GitHub Actions → 「Daily Fund Price Notification」 → 「Run workflow」で手動実行。
Slackチャンネルに通知が届くことを確認。

## ファンドの追加

`config/funds.yml` にエントリを追加:

```yaml
funds:
  - name: "eMAXIS Slim 新興国株式インデックス"
    short_name: "新興国株式"
    association_fund_cd: "0331C177"

  - name: "eMAXIS Slim 全世界株式 (オール・カントリー)"
    short_name: "全世界株式"
    association_fund_cd: "0331418A"
```

ファンドコード (`association_fund_cd`) は三菱UFJ AM APIの `/code_list` エンドポイントで検索できます:

```
https://developer.am.mufg.jp/code_list
```

> 注意: このAPIは三菱UFJアセットマネジメントが運用するファンドのみ対応しています。

## ローカル実行

```bash
pip install -r requirements.txt
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL_ID="C0123456789"
cd src && python main.py
```

## データソース

[三菱UFJアセットマネジメント ファンド情報API](https://www.am.mufg.jp/tool/webapi/)
- 認証不要・無料
- JSON形式のREST API
