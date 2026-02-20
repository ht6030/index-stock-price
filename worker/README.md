# Index Stock Price Worker (Cloudflare Workers)

MUFG API から投資信託の基準価額を取得し、Slack に通知する Cloudflare Workers 版。

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd worker
npm install
```

### 2. wrangler.toml の編集

`SLACK_CHANNEL_ID` に Slack チャンネル ID を設定:

```toml
[vars]
SLACK_CHANNEL_ID = "C0XXXXXXX"
```

### 3. シークレットの登録

```bash
npx wrangler secret put SLACK_BOT_TOKEN
# プロンプトに Slack Bot Token (xoxb-...) を入力
```

### 4. デプロイ

```bash
npx wrangler deploy
```

## ローカル開発

```bash
# 開発サーバー起動
npx wrangler dev

# ブラウザで http://localhost:8787/trigger にアクセスして手動実行

# Cron Trigger のテスト
npx wrangler dev --test-scheduled
# 別ターミナルから: curl "http://localhost:8787/__scheduled?cron=0+12+*+*+1-5"
```

## スケジュール

平日 21:00 JST (UTC 12:00) に自動実行。`wrangler.toml` の `crons` で変更可能。

## ファンドの追加

[src/index.ts](src/index.ts) の `FUNDS` 配列にエントリを追加:

```typescript
{
  name: "eMAXIS Slim 全世界株式 (オール・カントリー)",
  shortName: "全世界株式",
  associationFundCd: "0331418A",
  fundUrl: "https://emaxis.am.mufg.jp/fund/253425.html",
},
```
