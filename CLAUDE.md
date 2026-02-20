# CLAUDE.md

> **重要**: コードの変更・ファイル追加削除・設定変更・アーキテクチャ変更があった場合は、
> このファイルの該当箇所も必ず更新すること。README.md も同様に最新の状態を保つこと。

## プロジェクト概要

投資信託の基準価額を Cloudflare Workers で定期取得し、Slack に通知するシステム。

## 技術スタック

- **ランタイム**: Cloudflare Workers (TypeScript)
- **データソース**: 三菱UFJアセットマネジメント API (`https://developer.am.mufg.jp`)
- **通知**: Slack API (`chat.postMessage`)
- **定期実行**: Cron Triggers（平日 21:00 JST = UTC 12:00）

## ディレクトリ構成

```
worker/              # Cloudflare Workers プロジェクト
├── wrangler.toml    # Workers設定 (cron, env vars)
├── package.json
├── tsconfig.json
└── src/
    └── index.ts     # 全ロジック（API取得 + Slack通知）
```

## 重要なファイル

- `worker/src/index.ts` - メインロジック。ファンド設定もここに定義
- `worker/wrangler.toml` - Cron スケジュール、SLACK_CHANNEL_ID

## シークレット管理

- `SLACK_CHANNEL_ID` - `wrangler.toml` の `[vars]` に設定（公開値）
- `SLACK_BOT_TOKEN` - `wrangler secret put` で設定（非公開）

## デプロイ

```bash
cd worker && npx wrangler deploy
```

## MUFG API について

- エンドポイント: `/fund_information_latest/association_fund_cd/{code}`
- 認証不要だが、GitHub Actions の共有IPからはブロックされる（403）
- Cloudflare Workers に移行した理由はこの403対策
- ブラウザ User-Agent ヘッダーを設定してbot検出を回避
- 403時は指数バックオフでリトライ（最大3回）

## 開発時の注意

- Node.js が必要 (`brew install node`)
- ローカルテスト: `cd worker && npx wrangler dev` → `http://localhost:8787/trigger`
- ファンドの追加は `worker/src/index.ts` の `FUNDS` 配列に追加
