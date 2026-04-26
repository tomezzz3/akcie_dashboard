# Komplexní investiční/trading strategie a návrh aplikace pro generování signálů

Poslední revize: **2026-04-26 (UTC)**

## A) Shrnutí strategie

Cíl: vytvořit **multi-asset analytický engine** (akcie, ETF, krypto, volitelně komodity), který z heterogenních dat (fundament, technika, sentiment, makro, valuace, riziko) vyrobí:

1. **Attractiveness score (0–100)**,
2. **Signal class**: BUY / WATCH / HOLD / SELL / AVOID,
3. **Pravděpodobnostní scénáře** (bull/base/bear),
4. **Konkrétní trade plan** (entry, SL, TP, R/R, horizont),
5. **Auditovatelný komentář „proč“**.

### Multi-horizon koncept

- **Investor mode (3–36 měsíců)**: důraz na fundament + valuaci + makro.
- **Swing mode (2–30 dní)**: důraz na trend/momentum/volatilitu.
- **Crypto mode (intraday až 12 týdnů)**: důraz na momentum, flow a riziko likvidity.

### Pipeline signálu

`Raw data -> Feature engineering -> Normalizace -> Sub-skóre -> Composite score -> Režimové filtry (risk-on/off) -> Signal + Position sizing -> Alert + Evidence`

---

## B) Logika signálů

## 1) Vstupní logika (gating + score)

Nejdřív musí projít **gating podmínky**, pak se aplikuje skóre:

### Gating (must-pass)

- **Likvidita**: `ADV20 >= min_adv` (např. 10M USD pro US akcie, 5M USD pro ETF, u krypta min. notional volume).
- **Datová kvalita**: žádná klíčová metrika nesmí být starší než definovaný limit (`fundamental_staleness_days`, `price_staleness_minutes`).
- **Event risk guard**: pokud je earnings do 24h (akcie), signál se přepne na WATCH (pokud není explicitně earnings strategie).
- **Volatility cap**: pokud `ATR(14)/Close > max_vol_threshold`, aktivum může být jen WATCH/AVOID podle risk profilu.

### Composite signal mapping

- `Score >= 80` + trend OK -> **BUY**
- `65 <= Score < 80` -> **WATCH / BUY-light** (podle risk regime)
- `50 <= Score < 65` -> **HOLD/WATCH**
- `35 <= Score < 50` -> **SELL/HOLD-reduce**
- `Score < 35` -> **AVOID/SELL**

## 2) Pravděpodobnostní scénáře (bull/base/bear)

Použij směs modelů:

- `Expected return = w1*factor_model + w2*technical_projection + w3*valuation_reversion`
- Scénáře:
  - **Bull**: 20% pravděpodobnost,
  - **Base**: 50% pravděpodobnost,
  - **Bear**: 30% pravděpodobnost (u risk-off režimu lze posunout na 35–40%).

`Target price (base) = CurrentPrice * (1 + E[r]_base)`

`Upside% = (TargetPrice - CurrentPrice) / CurrentPrice * 100`

### Confidence score (0–100)

`Confidence = 0.35*DataQuality + 0.25*SignalAgreement + 0.20*RegimeStability + 0.20*LiquidityScore`

---

## C) Scoring model

## 1) Sub-skóre (0–100)

Každé sub-skóre vzniká z normalizovaných feature (z-score + clipping + percentile rank):

- **Fundamental Score**
- **Technical Score**
- **Momentum Score**
- **Valuation Score**
- **Quality Score**
- **Risk Penalty Score** (vyšší riziko = nižší body)
- **Sentiment Score**
- **Macro Score**

### Normalizace metrik

`norm(x) = min(100, max(0, 50 + 10*zscore(x)))`

Pro metriky, kde nižší je lepší (např. NetDebt/EBITDA), se použije inverze.

## 2) Váhy podle stylu

### Dlouhodobé investování

- Fundament 25%
- Valuace 20%
- Quality 15%
- Macro 15%
- Risk 10%
- Technical 7%
- Momentum 5%
- Sentiment 3%

### Swing trading

- Technical 30%
- Momentum 20%
- Risk 15%
- Sentiment 10%
- Macro 10%
- Fundament 8%
- Valuace 5%
- Quality 2%

### Dividendové investování

- Fundament 25%
- Valuace 20%
- Quality 20%
- Risk 10%
- Macro 10%
- Dividend Sustainability (v rámci fundamentu) + overweight
- Technical 8%
- Sentiment 4%
- Momentum 3%

### Růstové akcie

- Fundament (growth-heavy) 28%
- Momentum 20%
- Technical 15%
- Valuace 10%
- Quality 10%
- Sentiment 8%
- Macro 6%
- Risk 3%

### Kryptoměny

- Technical 28%
- Momentum 22%
- Risk 15%
- Sentiment 15%
- Macro (likvidita USD, rates) 10%
- On-chain/quality proxy 7%
- Relative valuation 3%

## 3) Fundamentální feature set (konkrétně)

- Growth: CAGR tržeb (3Y), EPS growth (TTM, forward 1Y), FCF growth.
- Profitability: gross margin trend, operating margin, ROIC, FCF margin.
- Balance sheet: NetDebt/EBITDA, Interest Coverage, Current Ratio.
- Valuace: P/E NTM, P/S, P/B, EV/EBITDA, FCF Yield.
- Shareholder return: dividend yield, payout ratio, buyback yield.
- Management/insider: insider net buying (90 dní), insider cluster buys.
- Analysts: EPS revisions (30/90 dní), target revisions.
- Earnings quality: surprise vs estimate, accruals proxy.
- Moat proxy: stability marží vs sektor, R&D intensity (kde relevantní).

---

## D) Risk management a stop loss pravidla

## 1) Portfolio-level pravidla

- **Max risk na obchod**: 0.5–1.0% NAV (retail), 0.25–0.75% (agresivní multi-signal portfolio).
- **Max sektorová expozice**: 20–30% (akcie), u krypta max 40% jedno téma (L1, DeFi, AI).
- **Max single-asset exposure**: 5–10% NAV dle likvidity.
- **Portfolio max drawdown kill-switch**: -10% soft (risk halve), -15% hard (stop new risk).

## 2) Position sizing

`PositionSize = AccountRiskUSD / StopDistanceUSD`

`AccountRiskUSD = NAV * risk_per_trade`

Volatility-adjusted sizing:

`AdjSize = PositionSize * min(1, TargetVol / AssetVol20)`

## 3) Stop-loss typy a použití

### a) ATR stop

- **Vzorec long**: `SL = Entry - k * ATR(14)` (k = 1.5 až 3.0)
- Vhodné: trend following, volatilní trhy, krypto.
- Nevhodné: extrémně nízká volatilita před earnings (falešné těsné stop-outs).

### b) Swing low/high stop

- Long SL pod posledním validním swing low (plus buffer 0.2–0.5 ATR).
- Vhodné: price action struktura, breakout retest setupy.
- Nevhodné: choppy trh bez jasných swingů.

### c) Volatility regime stop

- `SL distance = f(realized_vol, implied_vol)`
- Vhodné: režimové strategie, index/ETF, opční-aware systém.
- Nevhodné: když nemáš robustní vol data.

### d) Fixed percentage stop

- Např. 5%, 8%, 10%.
- Vhodné: jednoduchost, beginner režim, velmi likvidní ETF.
- Nevhodné: cross-asset systém (ignoruje specifickou volatilitu aktiva).

## 4) TP, trailing, time exits

- **TP1**: 1R, **TP2**: 2R až 3R.
- Po TP1 posun SL na BE (break-even).
- **Trailing**: `max(previous_trailing, Close - 2*ATR)`.
- **Time stop**: pokud po X svíčkách (např. 10 denních) trade nedosáhne alespoň +0.5R, redukce/exit.
- **Invalidation level**: technická/fundamentální podmínka, která ruší tezi (např. break pod weekly support + negativní EPS revize).

---

## E) Datové zdroje (free vs paid)

## 1) Ceny a market data

- **Free**: Yahoo Finance (neoficiální), Stooq, Alpha Vantage (omezené limity).
- **Paid/pro**: Polygon, Tiingo, IEX Cloud, Refinitiv, Bloomberg.

## 2) Fundamenty

- **Free/freemium**: Financial Modeling Prep, Alpha Vantage fundamentals, SEC EDGAR parsing.
- **Paid**: FactSet, S&P Capital IQ, Morningstar Direct, Refinitiv.

## 3) Krypto

- **Free/freemium**: Binance/Bybit/Kraken veřejná API, CoinGecko.
- **Paid**: Kaiko, CryptoCompare enterprise, CoinAPI.

## 4) Makro a ekonomika

- **Free**: FRED, ECB SDW, IMF data, OECD.
- **Paid**: Macrobond, Haver Analytics.

## 5) Earnings, insider, ratings, sentiment

- Earnings kalendář: Nasdaq API/feeds, Finnhub, Polygon (paid tiers).
- Insider: SEC Form 4 (EDGAR), OpenInsider.
- Analyst ratings: Finnhub/IEX/Refinitiv/Bloomberg.
- News sentiment: GDELT, RavenPack (paid), NewsAPI + vlastní NLP.
- Social sentiment: X/Twitter API (paid tiers), Reddit API, Stocktwits.

## 6) Doporučení pro robustní stack dat

MVP: Yahoo/FMP/FRED/CoinGecko + Finnhub (earnings/estimates).
Pro verzi Pro: Polygon + FactSet/CapIQ + Kaiko + RavenPack.

---

## F) Architektura aplikace

## 1) High-level

- **Frontend**: Next.js (TypeScript) + Tailwind + ECharts/TradingView widget.
- **Backend API**: Python FastAPI (analytics + orchestrace).
- **Model layer**: Python (pandas/polars, numpy, statsmodels, ta-lib).
- **DB**:
  - PostgreSQL (metadata, portfolio, signals),
  - TimescaleDB extension (time-series),
  - Redis (cache + queue),
  - S3 compatible storage (reporty/backtest artifacty).
- **Scheduler/orchestrace**: Celery + Redis/RabbitMQ nebo Prefect/Airflow.
- **Auth**: OAuth2 + JWT + optional SSO.
- **Notifications**: e-mail (SES/Sendgrid), Telegram bot, Discord webhook, Slack webhook, push (FCM/APNS).
- **Monitoring**: Prometheus + Grafana + OpenTelemetry + Sentry.

## 2) Datové tabulky (návrh)

- `assets(id, ticker, asset_type, exchange, sector, currency, is_active)`
- `prices(asset_id, ts, open, high, low, close, volume, source)`
- `fundamentals(asset_id, period_end, metric, value, source, asof_date)`
- `macro_series(series_id, ts, value, source)`
- `signals(id, asset_id, ts, score_total, signal, confidence, entry, sl, tp1, tp2, rr, horizon)`
- `signal_explanations(signal_id, pillar, text, importance)`
- `portfolios(id, user_id, name, base_ccy, risk_profile)`
- `positions(id, portfolio_id, asset_id, qty, avg_price, stop, take_profit, opened_at, status)`
- `orders(id, broker, external_order_id, status, requested_at, filled_at)`
- `backtests(id, user_id, strategy_name, params_json, metrics_json, artifact_url, created_at)`
- `alerts(id, user_id, channel, payload, status, sent_at)`
- `audit_logs(id, user_id, action, target, details_json, created_at)`

## 3) Workflow

1. Ingest job stáhne data (market/fundamental/makro/sentiment).
2. Feature engine spočítá indikátory a faktorové hodnoty.
3. Scoring service vytvoří sub-skóre a composite score.
4. Signal engine aplikuje gating + regime rules + risk module.
5. Execution adapter pošle alert nebo trade request.
6. Report service generuje PDF/CSV + AI komentář.

---

## G) Integrace s brokery a platformami

## 1) Kde lze exekvovat přes API

- **Interactive Brokers**: ano (TWS/IB Gateway API).
- **Alpaca**: ano (REST + streaming).
- **Binance**: ano (spot/futures API, dle regionálních omezení).
- **Coinbase Advanced**: ano.
- **MetaTrader**: nepřímo (bridge/EA/third-party connector), ne čisté univerzální REST.

## 2) Kde je spíš alert / omezené API

- **TradingView**: webhook alerty -> tvůj execution webhook (ne broker univerzální exekuce nativně přes TV pro všechny).
- **XTB**: API existuje (xAPI), ale dostupnost/podmínky dle regionu a účtu.
- **eToro**: veřejné trading API historicky omezené; typicky spíš semi-manual/alert workflow.
- **Degiro**: oficiální veřejné trading API je omezené/nepravidelné; obvykle bez produkční auto-exekuce.

## 3) Execution safety

- `paper/live` hard toggle.
- Povinné user confirmation pro live order nad risk threshold.
- Pre-trade checks: max size, max daily loss, symbol whitelist.

---

## H) Návrh UI dashboardu

## 1) Hlavní obrazovka

- Top bar: režim (Investor/Swing/Crypto), risk regime, poslední refresh.
- **Signal table**: ticker, cena, score, signal, confidence, upside/downside, SL/TP, R/R.
- **Heatmap sektorů**: performance + average score.
- **Risk panel**: VaR proxy, drawdown, koncentrace, otevřené riziko.

## 2) Detail aktiva

- Price chart (multi timeframe) + EMA20/50/200, RSI, MACD, BB, ATR.
- Fundamentals panel (growth/margins/debt/valuation/dividend).
- Sentiment feed (news + social trend).
- Scenario card: bull/base/bear s pravděpodobnostmi.
- Signal rationale: top 5 faktorů, které nejvíc přispěly ke skóre.

## 3) Další moduly

- Watchlist,
- Portfolio tracker,
- Backtest center,
- Paper trading blotter,
- Signal history & hit-rate,
- Export PDF/CSV.

---

## I) Backtesting metodika

## 1) Data hygiene

- Survivorship-bias free universe (historické konstituenty indexu, ne jen současné tickery).
- Corporate actions adjusted data (splity/dividendy).
- Point-in-time fundamentals (zabránit look-ahead bias).

## 2) Trading assumptions

- Transaction cost model: komise + spread + borrow fee (short).
- Slippage model: fixní bps + volatilita + participation rate.
- Execution lag: signál na close -> exekuce next open (nebo VWAP+1).

## 3) Validace

- In-sample / out-of-sample.
- Walk-forward optimization (rolling windows).
- Monte Carlo reshuffle pořadí obchodů pro robustnost equity curve.

## 4) Metriky

- CAGR,
- Sharpe,
- Sortino,
- Max drawdown,
- Calmar,
- Volatilita,
- Win rate,
- Profit factor,
- Avg win / Avg loss,
- Exposure,
- Turnover,
- Beta/alpha vs benchmark.

---

## J) MVP roadmapa

## Fáze 1 (4–6 týdnů)

- Universe: US akcie + top crypto.
- Data ingest: prices + základní fundamentals + FRED makro.
- Core scoring model (8 pilířů, jednoduché váhy).
- Dashboard + detail aktiva + watchlist.
- Základní alerty (e-mail + Telegram).

## Fáze 2 (3–5 týdnů)

- Paper trading modul.
- Jednoduchý backtest (daily bars, fees/slippage).
- Signal history + hit-rate panel.
- Export PDF/CSV.

## Fáze 3 (4+ týdnů)

- Broker integrace (Alpaca + Binance + IB paper).
- Pokročilé risk rules + regime detection.
- AI komentář k signálům (RAG nad interními daty + zprávy).

---

## K) Rozšíření do profesionální verze

- Multi-tenant architektura + RBAC.
- Alternativní data (credit card spend, web traffic, app usage).
- Options analytics (IV rank, skew, gamma exposure).
- Portfolio optimizer (Black-Litterman / HRP / CVaR constraints).
- Real-time stream processing (Kafka + Flink).
- Explainable AI layer (SHAP pro model-driven signály).

---

## L) Ukázkový výstup pro jedno aktivum (schema)

```json
{
  "asset_name": "Microsoft Corp.",
  "ticker": "MSFT",
  "asset_type": "equity",
  "current_price": 0.0,
  "target_price_base": 0.0,
  "expected_move_pct": 0.0,
  "signal": "WATCH",
  "confidence_score": 0,
  "scores": {
    "total": 0,
    "fundamental": 0,
    "technical": 0,
    "momentum": 0,
    "valuation": 0,
    "quality": 0,
    "risk": 0,
    "sentiment": 0,
    "macro": 0
  },
  "entry_zone": [0.0, 0.0],
  "stop_loss": {
    "method": "ATR_2x",
    "level": 0.0
  },
  "take_profit": {
    "tp1": 0.0,
    "tp2": 0.0
  },
  "risk_reward_ratio": 0.0,
  "time_horizon": "3-8 weeks",
  "fundamental_comment": "...",
  "technical_comment": "...",
  "key_risks": ["earnings volatility", "multiple compression"],
  "last_data_update_utc": "2026-04-26T00:00:00Z"
}
```

---

## M) Disclaimer (právní a bezpečnostní)

Tento systém je **analytický a vzdělávací nástroj**. Nejedná se o individuální investiční poradenství ani garanci výnosu. Uživatel nese plnou odpovědnost za investiční rozhodnutí. Minulá výkonnost negarantuje budoucí výsledky.

### Bezpečnostní standard

- API klíče šifrovat (KMS/Vault, AES-256 at rest).
- Oddělit `read-only` a `trading` oprávnění.
- Povinné 2FA pro live trading.
- Audit log všech akcí (včetně změn risk limitů).
- Rate limit + IP/device anomaly detection.
- User confirmation před live exekucí nad definovaný risk limit.
- Emergency kill switch (globální stop trading).
