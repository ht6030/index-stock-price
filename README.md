# index-stock-price

投資信託の基準価額を毎日自動取得し、Slackに通知するシステム。
Cloudflare Workers + Cron Triggers で平日21時 (JST) に定期実行。

## 機能

- 三菱UFJアセットマネジメント公式APIから基準価額を自動取得
- 前日比 (円・%) を表示
- 1ヶ月・1年の騰落率を表示
- Cloudflare Workers で平日21:00 JST に自動実行

## アーキテクチャ

```
Cloudflare Workers (TypeScript)
  → MUFG API (基準価額取得)
  → Slack API (通知送信)
```

## セットアップ

### 1. Slackアプリの作成

1. https://api.slack.com/apps にアクセス
2. 「Create New App」→「From scratch」を選択
3. アプリ名 (例: `Fund Monitor`) とワークスペースを指定して作成
4. 左メニュー「OAuth & Permissions」→「Bot Token Scopes」に以下を追加:
   - `chat:write`
5. ページ上部の「Install to Workspace」をクリック
6. **Bot User OAuth Token** (`xoxb-...`) をコピー

### 2. Slackチャンネルの準備

1. 通知先チャンネルを作成 (例: `#fund-prices`)
2. チャンネル名をクリック → 下部に表示される **チャンネルID** (`C0123456789`) をコピー
3. チャンネル内で `/invite @アプリ名` を入力してBotを招待

### 3. Cloudflare Workers のデプロイ

```bash
cd worker
npm install

# wrangler.toml の SLACK_CHANNEL_ID を設定済みであることを確認

# Cloudflare にログイン
npx wrangler login

# Slack Bot Token をシークレットとして登録
npx wrangler secret put SLACK_BOT_TOKEN

# デプロイ
npx wrangler deploy
```

### 4. 動作確認

```bash
curl https://index-stock-price.<your-subdomain>.workers.dev/trigger
```

Slackチャンネルに通知が届くことを確認。

## ファンドの追加

`worker/src/index.ts` の `FUNDS` 配列にエントリを追加:

```typescript
{
  name: "eMAXIS Slim 全世界株式 (オール・カントリー)",
  shortName: "全世界株式",
  associationFundCd: "0331418A",
  fundUrl: "https://emaxis.am.mufg.jp/fund/253425.html",
},
```

ファンドコード (`associationFundCd`) は三菱UFJ AM APIの `/code_list` エンドポイントで検索できます:

```
https://developer.am.mufg.jp/code_list
```

> 注意: このAPIは三菱UFJアセットマネジメントが運用するファンドのみ対応しています。

## ローカル開発

```bash
cd worker
npm install
npx wrangler dev

# ブラウザで http://localhost:8787/trigger にアクセスして手動実行
```

## データソース

[三菱UFJアセットマネジメント ファンド情報API](https://www.am.mufg.jp/tool/webapi/)
- 認証不要・無料
- JSON形式のREST API
