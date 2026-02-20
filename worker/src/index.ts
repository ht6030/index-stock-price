// ============================================================
// 監視対象ファンド設定
// ============================================================
interface FundConfig {
  name: string;
  shortName: string;
  associationFundCd: string;
  fundUrl: string;
}

const FUNDS: FundConfig[] = [
  {
    name: "eMAXIS Slim 新興国株式インデックス",
    shortName: "新興国株式",
    associationFundCd: "0331C177",
    fundUrl: "https://emaxis.am.mufg.jp/fund/252878.html",
  },
  // 追加例:
  // {
  //   name: "eMAXIS Slim 全世界株式 (オール・カントリー)",
  //   shortName: "全世界株式",
  //   associationFundCd: "0331418A",
  //   fundUrl: "https://emaxis.am.mufg.jp/fund/253425.html",
  // },
];

// ============================================================
// Slack メンション先ユーザーID
// ============================================================
const SLACK_MENTION_USER_ID = "U0ABQH0L71Q";

// ============================================================
// MUFG API
// ============================================================
const API_BASE = "https://developer.am.mufg.jp";

const BROWSER_HEADERS: Record<string, string> = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  Accept: "application/json, text/plain, */*",
  "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
};

interface FundPrice {
  fundName: string;
  date: string; // YYYY/MM/DD
  nav: number;
  dailyChange: number;
  dailyChangePct: number;
  pctChange1m: string;
  pctChange1y: string;
}

async function fetchLatest(
  associationFundCd: string,
  maxRetries = 3
): Promise<Record<string, unknown>> {
  const url = `${API_BASE}/fund_information_latest/association_fund_cd/${associationFundCd}`;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const resp = await fetch(url, { headers: BROWSER_HEADERS });

    if (resp.status === 403 && attempt < maxRetries - 1) {
      const waitMs = (attempt + 1) * 5000;
      console.log(
        `403 error, retrying in ${waitMs / 1000}s... (attempt ${attempt + 1}/${maxRetries})`
      );
      await sleep(waitMs);
      continue;
    }

    if (!resp.ok) {
      throw new Error(`MUFG API error: ${resp.status} ${resp.statusText}`);
    }

    const data = (await resp.json()) as { datasets?: Record<string, unknown>[] };
    const items = data.datasets ?? [];
    if (items.length === 0) {
      throw new Error(`No data returned for fund ${associationFundCd}`);
    }
    return items[0];
  }

  throw new Error(`Failed after ${maxRetries} retries for fund ${associationFundCd}`);
}

function parseFundPrice(
  raw: Record<string, unknown>,
  fundName: string
): FundPrice {
  const baseDateStr = String(raw.base_date);
  const y = baseDateStr.slice(0, 4);
  const m = baseDateStr.slice(4, 6);
  const d = baseDateStr.slice(6, 8);

  const cmp = String(raw.cmp_prev_day ?? "0");
  const dailyChange = cmp && cmp !== "-" ? parseInt(cmp, 10) : 0;

  const pct = String(raw.percentage_change ?? "0");
  const dailyChangePct = pct && pct !== "-" ? parseFloat(pct) : 0;

  return {
    fundName,
    date: `${y}/${m}/${d}`,
    nav: Number(raw.nav),
    dailyChange,
    dailyChangePct,
    pctChange1m: String(raw.percentage_change_1m ?? "-"),
    pctChange1y: String(raw.percentage_change_1y ?? "-"),
  };
}

// ============================================================
// Slack 通知
// ============================================================
async function postSlackMessage(
  token: string,
  channelId: string,
  price: FundPrice,
  fundUrl: string
): Promise<void> {
  const sign = price.dailyChange >= 0 ? "+" : "";
  const trend =
    price.dailyChange >= 0
      ? ":chart_with_upwards_trend:"
      : ":chart_with_downwards_trend:";

  const pct1m = price.pctChange1m !== "-" ? price.pctChange1m : "N/A";
  const pct1y = price.pctChange1y !== "-" ? price.pctChange1y : "N/A";

  const message = [
    `<@${SLACK_MENTION_USER_ID}> ${trend} *${price.fundName}*`,
    `:calendar: ${price.date}`,
    `:moneybag: 基準価額: *${price.nav.toLocaleString()}円*`,
    `前日比: *${sign}${price.dailyChange.toLocaleString()}円* (${sign}${price.dailyChangePct}%)`,
    `1ヶ月: ${pct1m}% | 1年: ${pct1y}%`,
    `:link: <${fundUrl}|詳細・長期チャートを見る>`,
  ].join("\n");

  const resp = await fetch("https://slack.com/api/chat.postMessage", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      channel: channelId,
      text: message,
      mrkdwn: true,
    }),
  });

  const result = (await resp.json()) as { ok: boolean; error?: string };
  if (!result.ok) {
    throw new Error(`Slack API error: ${result.error}`);
  }
}

// ============================================================
// ユーティリティ
// ============================================================
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ============================================================
// メイン処理
// ============================================================
async function processFunds(env: Env): Promise<void> {
  for (const fund of FUNDS) {
    console.log(`Processing: ${fund.name}`);
    try {
      const raw = await fetchLatest(fund.associationFundCd);
      const price = parseFundPrice(raw, fund.name);
      console.log(`  Latest: ${price.nav.toLocaleString()} yen (${price.date})`);

      await postSlackMessage(
        env.SLACK_BOT_TOKEN,
        env.SLACK_CHANNEL_ID,
        price,
        fund.fundUrl
      );
      console.log("  Slack notification sent");
    } catch (e) {
      console.error(`  Error processing ${fund.name}:`, e);
    }
  }
  console.log("Done.");
}

// ============================================================
// Worker エントリポイント
// ============================================================
export interface Env {
  SLACK_BOT_TOKEN: string;
  SLACK_CHANNEL_ID: string;
}

export default {
  // Cron Trigger（定期実行）
  async scheduled(
    _controller: ScheduledController,
    env: Env,
    _ctx: ExecutionContext
  ): Promise<void> {
    await processFunds(env);
  },

  // HTTP リクエスト（手動テスト用）
  async fetch(
    request: Request,
    env: Env,
    _ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/trigger") {
      await processFunds(env);
      return new Response("OK - notifications sent", { status: 200 });
    }

    return new Response(
      "Index Stock Price Worker\n\nGET /trigger - 手動実行",
      { status: 200 }
    );
  },
};
