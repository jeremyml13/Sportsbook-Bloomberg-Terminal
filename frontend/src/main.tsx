import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { Activity, AlertTriangle, ArrowLeft, Clock, Newspaper, Radio, Search, Star, Trash2, TrendingUp } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./styles.css";

type MarketType = "spread" | "moneyline" | "total";

type Team = {
  id: string;
  name: string;
  abbreviation: string | null;
};

type OddsLine = {
  sportsbook: string;
  selection: string;
  market_type: MarketType;
  line: number | null;
  odds_american: number;
  implied_probability: number;
  snapshot_time: string;
};

type CurrentMarkets = {
  spread: OddsLine[];
  moneyline: OddsLine[];
  total: OddsLine[];
};

type MarketSignal = {
  signal_type: string;
  market_type: MarketType;
  severity: "info" | "warning" | "placeholder";
  message: string;
  value: number | null;
  detected_at: string;
};

type OddsHistoryPoint = {
  timestamp: string;
  sportsbook: string;
  market_type: MarketType;
  selection: string;
  line: number | null;
  odds_american: number;
};

type GameSummary = {
  id: string;
  sport_key: string;
  commence_time: string;
  home_team: Team;
  away_team: Team;
  current_markets: CurrentMarkets;
  opening_markets: CurrentMarkets | null;
  signals: MarketSignal[];
  volatility_score: number;
  book_disagreement_score: number;
  opportunity_score: number;
  opportunity_reasons: string[];
  best_prices: BestPrice[];
  no_vig_moneyline: NoVigProbability[];
  price_alerts: PriceAlert[];
};

type GameDetail = GameSummary & {
  odds_history: OddsHistoryPoint[];
  book_table: OddsLine[];
  movement_alerts: MovementAlert[];
};

type BestPrice = {
  market_type: MarketType;
  selection: string;
  sportsbook: string;
  line: number | null;
  odds_american: number;
  implied_probability: number;
};

type NoVigProbability = {
  selection: string;
  fair_probability: number;
  best_sportsbook: string | null;
  best_odds_american: number | null;
};

type PriceAlert = {
  market_type: MarketType;
  selection: string;
  sportsbook: string;
  line: number | null;
  odds_american: number;
  edge_to_market: number;
  message: string;
};

type MovementAlert = {
  sportsbook: string;
  market_type: MarketType;
  selection: string;
  opening_line: number | null;
  current_line: number | null;
  line_delta: number | null;
  opening_odds_american: number;
  current_odds_american: number;
  odds_delta: number;
  first_seen: string;
  last_seen: string;
  message: string;
};

type PlayerInjury = {
  external_player_id: string;
  display_name: string;
  team: string | null;
  position: string | null;
  status: string | null;
  injury_status: string | null;
  injury_body_part: string | null;
  injury_start_date: string | null;
  injury_notes: string | null;
  upcoming_game_external_id: string | null;
  observed_at: string;
};

type PlayerNews = {
  external_news_id: string;
  title: string;
  content: string | null;
  source: string | null;
  url: string | null;
  original_source: string | null;
  original_source_url: string | null;
  team: string | null;
  team2: string | null;
  categories: string | null;
  updated_at: string | null;
  source_time_ago: string | null;
};

type GameContext = {
  game_id: string;
  teams: string[];
  injuries: PlayerInjury[];
  injury_events: PlayerInjuryEvent[];
  news: PlayerNews[];
};

type PlayerInjuryEvent = {
  external_player_id: string;
  display_name: string;
  team: string | null;
  position: string | null;
  event_type: string;
  previous_status: string | null;
  current_status: string | null;
  previous_body_part: string | null;
  current_body_part: string | null;
  previous_notes: string | null;
  current_notes: string | null;
  detected_at: string;
};

type ChartMode = "home_spread" | "moneyline" | "total";
type ViewMode = "board" | "opportunities" | "watchlist" | "notebook";

type SavedBetIdea = {
  id: string;
  game_id: string;
  game_label: string;
  selection: string;
  market_type: MarketType;
  sportsbook: string;
  line: number | null;
  odds_american: number;
  probability: number;
  ev_per_100: number;
  quarter_kelly: number;
  note: string;
  created_at: string;
};

const CHART_MODES: { key: ChartMode; label: string; description: string }[] = [
  { key: "home_spread", label: "Home Spread", description: "Home team line by sportsbook" },
  { key: "moneyline", label: "Moneyline", description: "Home team moneyline by sportsbook" },
  { key: "total", label: "Total", description: "Over total by sportsbook" },
];

const API_BASE = "http://127.0.0.1:8000";
const BOOK_COLORS = ["#22c55e", "#38bdf8", "#f59e0b", "#a78bfa", "#f472b6", "#14b8a6", "#eab308", "#fb7185", "#818cf8"];
const WATCHLIST_STORAGE_KEY = "sports-terminal-watchlist";
const BET_IDEAS_STORAGE_KEY = "sports-terminal-bet-ideas";

function formatOdds(value: number) {
  return value > 0 ? `+${value}` : String(value);
}

function formatLine(value: number | null) {
  if (value === null) return "-";
  return value > 0 ? `+${value}` : String(value);
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatSignedDollars(value: number) {
  const sign = value >= 0 ? "+" : "-";
  return `${sign}$${Math.abs(value).toFixed(2)}`;
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

function firstLine(markets: OddsLine[], sportsbook = "DraftKings") {
  return markets.find((line) => line.sportsbook === sportsbook) ?? markets[0];
}

function moneylineText(game: GameSummary) {
  const home = game.current_markets.moneyline.find((line) => line.selection === game.home_team.name);
  const away = game.current_markets.moneyline.find((line) => line.selection === game.away_team.name);
  if (!home || !away) return "-";
  return `${game.home_team.abbreviation} ${formatOdds(home.odds_american)} / ${game.away_team.abbreviation} ${formatOdds(away.odds_american)}`;
}

function spreadText(game: GameSummary) {
  const line = firstLine(game.current_markets.spread);
  return `${game.home_team.abbreviation} ${formatLine(line?.line ?? null)}`;
}

function openingSpreadText(game: GameSummary) {
  const line = firstLine(game.opening_markets?.spread ?? []);
  return `${game.home_team.abbreviation} ${formatLine(line?.line ?? null)}`;
}

function totalText(game: GameSummary) {
  const line = firstLine(game.current_markets.total);
  return line?.line?.toFixed(1) ?? "-";
}

function gameLabel(game: GameSummary) {
  return `${game.away_team.abbreviation} at ${game.home_team.abbreviation}`;
}

function gameSearchText(game: GameSummary) {
  return [
    game.home_team.name,
    game.home_team.abbreviation,
    game.away_team.name,
    game.away_team.abbreviation,
    ...game.opportunity_reasons,
    ...game.signals.map((signal) => signal.signal_type),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function marketRegimes(game: GameSummary) {
  const regimes: string[] = [];
  if (game.price_alerts.length) regimes.push("Stale Price");
  if (game.book_disagreement_score >= 1) regimes.push("High Disagreement");
  if (game.volatility_score >= 0.5) regimes.push("Volatile");
  if (game.signals.some((signal) => signal.severity === "warning")) regimes.push("Signal Active");
  if (!regimes.length) regimes.push("Quiet Market");
  return regimes;
}

function signalClass(signal: MarketSignal) {
  if (signal.severity === "warning") return "border-amber-400/50 bg-amber-400/10 text-amber-100";
  if (signal.severity === "placeholder") return "border-slate-500/70 bg-slate-800 text-slate-300";
  return "border-cyan-400/40 bg-cyan-400/10 text-cyan-100";
}

function SignalBadge({ signal }: { signal: MarketSignal }) {
  return (
    <div className={`rounded-md border px-3 py-2 ${signalClass(signal)}`}>
      <div className="flex items-center gap-2 text-xs font-semibold uppercase">
        <AlertTriangle className="h-3.5 w-3.5" />
        {signal.signal_type}
      </div>
      <p className="mt-1 text-xs leading-5 text-slate-300">{signal.message}</p>
    </div>
  );
}

function profitPerDollar(odds: number) {
  return odds > 0 ? odds / 100 : 100 / Math.abs(odds);
}

function expectedValuePer100(probability: number, odds: number) {
  return (probability * profitPerDollar(odds) - (1 - probability)) * 100;
}

function kellyFraction(probability: number, odds: number) {
  const profit = profitPerDollar(odds);
  return Math.max(0, (probability * profit - (1 - probability)) / profit);
}

function readStoredJson<T>(key: string, fallback: T): T {
  try {
    const stored = window.localStorage.getItem(key);
    return stored ? (JSON.parse(stored) as T) : fallback;
  } catch {
    return fallback;
  }
}

function InjuryNewsPanel({ context }: { context: GameContext | null }) {
  const injuries = context?.injuries ?? [];
  const injuryEvents = context?.injury_events ?? [];
  const news = context?.news ?? [];

  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Newspaper className="h-4 w-4 text-cyan-300" />
          <h3 className="text-sm font-semibold uppercase text-slate-300">Injuries & News</h3>
        </div>
        <span className="text-xs font-medium text-slate-500">{context?.teams.join(" / ") ?? "Loading"}</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          {injuryEvents.length ? (
            <div className="mb-3 rounded-md border border-amber-400/30 bg-amber-400/10 px-3 py-2">
              <div className="mb-2 text-xs font-semibold uppercase text-amber-200">Recent Injury Report Changes</div>
              <div className="space-y-2">
                {injuryEvents.slice(0, 3).map((event) => (
                  <div key={`${event.external_player_id}-${event.detected_at}`} className="text-xs leading-5 text-slate-300">
                    <span className="font-semibold text-slate-100">{event.display_name}</span>
                    {` ${event.event_type === "new_injury" ? "added" : "updated"} `}
                    <span className="text-amber-200">{event.current_status ?? "injury report"}</span>
                    <span className="text-slate-500"> · {event.team}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Player Injuries</div>
          <div className="space-y-2">
            {injuries.length ? (
              injuries.slice(0, 6).map((injury) => (
                <div key={`${injury.external_player_id}-${injury.team}-${injury.injury_status}`} className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-slate-100">{injury.display_name}</div>
                      <div className="mt-1 text-xs text-slate-500">
                        {[injury.team, injury.position, injury.status].filter(Boolean).join(" · ")}
                      </div>
                    </div>
                    {injury.injury_status ? (
                      <span className="rounded border border-amber-400/40 bg-amber-400/10 px-2 py-1 text-xs font-semibold text-amber-200">
                        {injury.injury_status}
                      </span>
                    ) : null}
                  </div>
                  {injury.injury_body_part || injury.injury_notes ? (
                    <p className="mt-2 text-xs leading-5 text-slate-400">
                      {[injury.injury_body_part, injury.injury_notes].filter(Boolean).join(" — ")}
                    </p>
                  ) : null}
                </div>
              ))
            ) : (
              <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-4 text-sm text-slate-500">No matching injuries found.</div>
            )}
          </div>
        </div>

        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-slate-500">News Updates</div>
          <div className="space-y-2">
            {news.length ? (
              news.slice(0, 5).map((item) => (
                <a
                  key={item.external_news_id}
                  href={item.url ?? undefined}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-md border border-slate-800 bg-slate-950 px-3 py-2 transition hover:border-cyan-500/70"
                >
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>{[item.team, item.team2].filter(Boolean).join(" / ")}</span>
                    <span>{item.source_time_ago ?? (item.updated_at ? formatTime(item.updated_at) : "")}</span>
                    <span>{item.source}</span>
                  </div>
                  <div className="mt-1 text-sm font-semibold leading-5 text-slate-100">{item.title}</div>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{item.content}</p>
                </a>
              ))
            ) : (
              <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-4 text-sm text-slate-500">No matching news found.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EvCalculator({ detail }: { detail: GameDetail }) {
  const moneylinePrices = detail.best_prices.filter((line) => line.market_type === "moneyline");
  const defaults = useMemo(
    () =>
      Object.fromEntries(
        detail.no_vig_moneyline.map((row) => [row.selection, Math.round(row.fair_probability * 1000) / 10]),
      ) as Record<string, number>,
    [detail.no_vig_moneyline],
  );
  const [probabilities, setProbabilities] = useState<Record<string, number>>(defaults);

  useEffect(() => {
    setProbabilities(defaults);
  }, [defaults]);

  if (!moneylinePrices.length) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="mb-2 text-xs font-semibold uppercase text-slate-500">EV Calculator</div>
      <div className="grid gap-3 lg:grid-cols-2">
        {moneylinePrices.map((line) => {
          const probability = probabilities[line.selection] ?? 50;
          const probabilityDecimal = probability / 100;
          const ev = expectedValuePer100(probabilityDecimal, line.odds_american);
          const edge = probabilityDecimal - line.implied_probability;
          const kelly = kellyFraction(probabilityDecimal, line.odds_american);
          const isPositive = ev >= 0;

          return (
            <div key={`${line.selection}-${line.sportsbook}-${line.odds_american}`} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">{line.selection}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    Best {formatOdds(line.odds_american)} at {line.sportsbook}
                  </div>
                </div>
                <div className={`rounded border px-2 py-1 text-xs font-semibold ${isPositive ? "border-emerald-400/40 text-emerald-200" : "border-rose-400/40 text-rose-200"}`}>
                  {formatSignedDollars(ev)} / $100
                </div>
              </div>

              <div className="mt-3 flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="99"
                  step="0.5"
                  value={probability}
                  onChange={(event) => {
                    setProbabilities((current) => ({
                      ...current,
                      [line.selection]: Number(event.target.value),
                    }));
                  }}
                  className="w-full accent-cyan-400"
                  aria-label={`${line.selection} win probability`}
                />
                <input
                  type="number"
                  min="1"
                  max="99"
                  step="0.5"
                  value={probability}
                  onChange={(event) => {
                    const nextValue = Math.min(99, Math.max(1, Number(event.target.value)));
                    setProbabilities((current) => ({
                      ...current,
                      [line.selection]: Number.isNaN(nextValue) ? probability : nextValue,
                    }));
                  }}
                  className="w-20 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-right text-sm font-semibold text-slate-100"
                  aria-label={`${line.selection} win probability percent`}
                />
              </div>

              <div className="mt-2 grid gap-2 sm:grid-cols-3">
                <Metric label="Your Probability" value={`${probability.toFixed(1)}%`} />
                <Metric label="Edge vs Price" value={`${(edge * 100).toFixed(1)} pp`} />
                <Metric label="Quarter Kelly" value={`${((kelly / 4) * 100).toFixed(1)}%`} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function QuantPanel({ detail }: { detail: GameDetail }) {
  const bestMoneylines = detail.best_prices.filter((line) => line.market_type === "moneyline").slice(0, 2);
  const bestSpreads = detail.best_prices.filter((line) => line.market_type === "spread").slice(0, 2);
  const bestTotals = detail.best_prices.filter((line) => line.market_type === "total").slice(0, 2);

  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="h-4 w-4 text-cyan-300" />
        <h3 className="text-sm font-semibold uppercase text-slate-300">Quant Snapshot</h3>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Best Available Prices</div>
          <div className="grid gap-2 md:grid-cols-3">
            {[
              ["Moneyline", bestMoneylines],
              ["Spread", bestSpreads],
              ["Total", bestTotals],
            ].map(([label, rows]) => (
              <div key={label as string} className="rounded-md border border-slate-800 bg-slate-950 p-3">
                <div className="mb-2 text-xs font-semibold uppercase text-slate-500">{label as string}</div>
                {(rows as BestPrice[]).map((row) => (
                  <div key={`${row.market_type}-${row.selection}-${row.line}`} className="mb-2 last:mb-0">
                    <div className="text-sm font-semibold text-slate-100">
                      {row.selection} {row.line !== null ? formatLine(row.line) : ""} {formatOdds(row.odds_american)}
                    </div>
                    <div className="text-xs text-slate-500">{row.sportsbook}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-slate-500">No-Vig Moneyline</div>
          <div className="grid gap-2 md:grid-cols-2">
            {detail.no_vig_moneyline.map((row) => (
              <div key={row.selection} className="rounded-md border border-slate-800 bg-slate-950 p-3">
                <div className="text-sm font-semibold text-slate-100">{row.selection}</div>
                <div className="mt-1 text-2xl font-semibold text-cyan-200">{formatPercent(row.fair_probability)}</div>
                <div className="mt-1 text-xs text-slate-500">
                  Best {row.best_odds_american !== null ? formatOdds(row.best_odds_american) : "-"} at {row.best_sportsbook ?? "-"}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <EvCalculator detail={detail} />

      <div className="mt-4">
        <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Price Alerts</div>
        <div className="grid gap-2 lg:grid-cols-2">
          {detail.price_alerts.length ? (
            detail.price_alerts.map((alert) => (
              <div key={`${alert.market_type}-${alert.selection}-${alert.sportsbook}-${alert.line}`} className="rounded-md border border-emerald-400/30 bg-emerald-400/10 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-100">
                      {alert.selection} {alert.line !== null ? formatLine(alert.line) : ""} {formatOdds(alert.odds_american)}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">{alert.message}</div>
                  </div>
                  <span className="rounded border border-emerald-400/40 px-2 py-1 text-xs font-semibold text-emerald-200">
                    {alert.edge_to_market.toFixed(1)} pp
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-4 text-sm text-slate-500">
              No stale-price alerts on the latest snapshot.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MovementPanel({ alerts }: { alerts: MovementAlert[] }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-cyan-300" />
        <h3 className="text-sm font-semibold uppercase text-slate-300">Line Movement Alerts</h3>
      </div>
      <div className="grid gap-2 lg:grid-cols-2">
        {alerts.length ? (
          alerts.map((alert) => (
            <div key={`${alert.sportsbook}-${alert.market_type}-${alert.selection}`} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">{alert.selection}</div>
                  <div className="mt-1 text-xs capitalize text-slate-500">
                    {alert.sportsbook} · {alert.market_type}
                  </div>
                </div>
                <div className="rounded border border-cyan-400/30 px-2 py-1 text-xs font-semibold text-cyan-200">
                  {alert.odds_delta > 0 ? "+" : ""}
                  {alert.odds_delta}c
                </div>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-400">{alert.message}</p>
              <div className="mt-2 grid gap-2 sm:grid-cols-3">
                <Metric label="Open" value={`${formatLine(alert.opening_line)} ${formatOdds(alert.opening_odds_american)}`} />
                <Metric label="Current" value={`${formatLine(alert.current_line)} ${formatOdds(alert.current_odds_american)}`} />
                <Metric label="Line Move" value={alert.line_delta === null ? "-" : formatLine(alert.line_delta)} />
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-4 text-sm text-slate-500">
            No material movement yet. This will populate after multiple odds refreshes.
          </div>
        )}
      </div>
    </div>
  );
}

function BetIdeaPanel({ detail, onSave }: { detail: GameDetail; onSave: (idea: SavedBetIdea) => void }) {
  const candidates = detail.best_prices;
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selectedLine = candidates[selectedIndex] ?? candidates[0];
  const fairProbability = detail.no_vig_moneyline.find((row) => row.selection === selectedLine?.selection)?.fair_probability;
  const [probability, setProbability] = useState(50);
  const [note, setNote] = useState("");

  useEffect(() => {
    setSelectedIndex(0);
  }, [detail.id]);

  useEffect(() => {
    setProbability(fairProbability ? Math.round(fairProbability * 1000) / 10 : 50);
  }, [fairProbability, selectedLine?.selection]);

  if (!selectedLine) {
    return null;
  }

  const probabilityDecimal = probability / 100;
  const ev = expectedValuePer100(probabilityDecimal, selectedLine.odds_american);
  const quarterKelly = kellyFraction(probabilityDecimal, selectedLine.odds_american) / 4;

  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
      <div className="mb-4 flex items-center gap-2">
        <Star className="h-4 w-4 text-cyan-300" />
        <h3 className="text-sm font-semibold uppercase text-slate-300">Bet Idea Notebook</h3>
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px]">
        <select
          value={selectedIndex}
          onChange={(event) => setSelectedIndex(Number(event.target.value))}
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm font-semibold text-slate-100"
        >
          {candidates.map((line, index) => (
            <option key={`${line.market_type}-${line.selection}-${line.sportsbook}-${line.line}`} value={index}>
              {line.market_type.toUpperCase()} · {line.selection} {line.line !== null ? formatLine(line.line) : ""} {formatOdds(line.odds_american)} · {line.sportsbook}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="1"
          max="99"
          step="0.5"
          value={probability}
          onChange={(event) => setProbability(Math.min(99, Math.max(1, Number(event.target.value))))}
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm font-semibold text-slate-100"
          aria-label="Fair probability"
        />
      </div>
      <textarea
        value={note}
        onChange={(event) => setNote(event.target.value)}
        className="mt-3 min-h-20 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-600"
        placeholder="Thesis, injury angle, model note, or price target"
      />
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        <Metric label="EV / $100" value={formatSignedDollars(ev)} />
        <Metric label="Edge vs Price" value={`${((probabilityDecimal - selectedLine.implied_probability) * 100).toFixed(1)} pp`} />
        <Metric label="Quarter Kelly" value={`${(quarterKelly * 100).toFixed(1)}%`} />
      </div>
      <button
        type="button"
        onClick={() => {
          onSave({
            id: `${detail.id}-${selectedLine.market_type}-${selectedLine.selection}-${Date.now()}`,
            game_id: detail.id,
            game_label: gameLabel(detail),
            selection: selectedLine.selection,
            market_type: selectedLine.market_type,
            sportsbook: selectedLine.sportsbook,
            line: selectedLine.line,
            odds_american: selectedLine.odds_american,
            probability,
            ev_per_100: ev,
            quarter_kelly: quarterKelly,
            note,
            created_at: new Date().toISOString(),
          });
          setNote("");
        }}
        className="mt-3 rounded-md border border-cyan-400/50 bg-cyan-400/10 px-3 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-400/20"
      >
        Save Bet Idea
      </button>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2">
      <div className="text-[11px] font-semibold uppercase text-slate-500">{label}</div>
      <div className="mt-1 text-sm font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900/80 p-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-50">{value}</div>
    </div>
  );
}

function CommandBar({
  command,
  games,
  onCommandChange,
  onSelectGame,
  onSetView,
}: {
  command: string;
  games: GameSummary[];
  onCommandChange: (value: string) => void;
  onSelectGame: (id: string) => void;
  onSetView: (view: ViewMode) => void;
}) {
  const normalized = command.trim().toLowerCase();
  const matches = normalized
    ? games.filter((game) => gameSearchText(game).includes(normalized)).slice(0, 5)
    : [];

  function submitCommand(event: React.FormEvent) {
    event.preventDefault();
    const value = command.trim().toLowerCase();
    if (["opp", "opps", "opportunity", "opportunities", "ev", "steam"].includes(value)) {
      onSetView("opportunities");
      return;
    }
    if (["watch", "watchlist", "pin", "pinned"].includes(value)) {
      onSetView("watchlist");
      return;
    }
    if (["note", "notes", "notebook", "bets", "ideas"].includes(value)) {
      onSetView("notebook");
      return;
    }
    if (["board", "mlb", "games"].includes(value)) {
      onSetView("board");
      return;
    }
    if (matches[0]) {
      onSelectGame(matches[0].id);
    }
  }

  return (
    <div className="relative">
      <form onSubmit={submitCommand} className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-950 px-3 py-2">
        <Search className="h-4 w-4 text-slate-500" />
        <input
          value={command}
          onChange={(event) => onCommandChange(event.target.value)}
          className="w-full bg-transparent text-sm font-semibold text-slate-100 outline-none placeholder:text-slate-600"
          placeholder="Terminal command"
        />
      </form>
      {matches.length ? (
        <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-md border border-slate-800 bg-slate-950 shadow-xl">
          {matches.map((game) => (
            <button
              key={game.id}
              type="button"
              onClick={() => onSelectGame(game.id)}
              className="flex w-full items-center justify-between gap-3 border-b border-slate-800 px-3 py-2 text-left last:border-b-0 hover:bg-slate-900"
            >
              <span className="text-sm font-semibold text-slate-100">{gameLabel(game)}</span>
              <span className="text-xs text-cyan-200">OPP {game.opportunity_score.toFixed(0)}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function OpportunityBoard({ games, onSelectGame }: { games: GameSummary[]; onSelectGame: (id: string) => void }) {
  const rows = games
    .filter((game) => game.opportunity_score > 0 || game.price_alerts.length > 0)
    .sort((a, b) => b.opportunity_score - a.opportunity_score);

  return (
    <section className="rounded-md border border-slate-800 bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-cyan-300" />
          <h2 className="text-sm font-semibold uppercase text-slate-300">Top Opportunities</h2>
        </div>
        <span className="text-xs font-semibold text-slate-500">{rows.length} active spots</span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-950 text-left text-[11px] font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Game</th>
              <th className="px-4 py-3">Opp</th>
              <th className="px-4 py-3">Best ML</th>
              <th className="px-4 py-3">Price Alert</th>
              <th className="px-4 py-3">Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.length ? (
              rows.map((game) => {
                const bestMl = game.best_prices.find((line) => line.market_type === "moneyline");
                const alert = game.price_alerts[0];
                return (
                  <tr key={game.id} className="bg-slate-900 hover:bg-slate-900/70">
                    <td className="px-4 py-3">
                      <button type="button" onClick={() => onSelectGame(game.id)} className="text-left font-semibold text-slate-100 hover:text-cyan-200">
                        {gameLabel(game)}
                      </button>
                      <div className="mt-1 text-xs text-slate-500">{formatTime(game.commence_time)}</div>
                    </td>
                    <td className="px-4 py-3 text-cyan-200">{game.opportunity_score.toFixed(1)}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {bestMl ? `${bestMl.selection} ${formatOdds(bestMl.odds_american)} · ${bestMl.sportsbook}` : "-"}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {alert ? `${alert.selection} ${formatOdds(alert.odds_american)} · ${alert.edge_to_market.toFixed(1)} pp` : "-"}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{game.opportunity_reasons[0] ?? "Market watchlist candidate."}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={5} className="bg-slate-900 px-4 py-5 text-slate-500">
                  No opportunity-ranked games yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function WatchlistBoard({
  games,
  watchlist,
  onSelectGame,
  onToggleWatch,
}: {
  games: GameSummary[];
  watchlist: string[];
  onSelectGame: (id: string) => void;
  onToggleWatch: (id: string) => void;
}) {
  const watchedGames = games.filter((game) => watchlist.includes(game.id));

  return (
    <section className="grid gap-4">
      {watchedGames.length ? (
        watchedGames.map((game) => (
          <GameCard key={game.id} game={game} watched onSelect={onSelectGame} onToggleWatch={onToggleWatch} />
        ))
      ) : (
        <div className="rounded-md border border-slate-800 bg-slate-900 px-4 py-5 text-sm text-slate-500">
          No games are pinned yet. Open a game and use the watchlist button.
        </div>
      )}
    </section>
  );
}

function NotebookView({
  ideas,
  onDelete,
  onSelectGame,
}: {
  ideas: SavedBetIdea[];
  onDelete: (id: string) => void;
  onSelectGame: (id: string) => void;
}) {
  return (
    <section className="rounded-md border border-slate-800 bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <Star className="h-4 w-4 text-cyan-300" />
          <h2 className="text-sm font-semibold uppercase text-slate-300">Bet Idea Notebook</h2>
        </div>
        <span className="text-xs font-semibold text-slate-500">{ideas.length} saved ideas</span>
      </div>
      <div className="grid gap-3 p-4">
        {ideas.length ? (
          ideas.map((idea) => (
            <div key={idea.id} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <button type="button" onClick={() => onSelectGame(idea.game_id)} className="text-left text-sm font-semibold text-slate-100 hover:text-cyan-200">
                    {idea.game_label}
                  </button>
                  <div className="mt-1 text-xs text-slate-500">{formatDateTime(idea.created_at)}</div>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(idea.id)}
                  className="rounded border border-slate-700 p-1.5 text-slate-400 hover:border-rose-400/50 hover:text-rose-200"
                  aria-label="Delete bet idea"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-5">
                <Metric label="Bet" value={`${idea.selection} ${idea.line !== null ? formatLine(idea.line) : ""}`} />
                <Metric label="Odds" value={`${formatOdds(idea.odds_american)} ${idea.sportsbook}`} />
                <Metric label="Prob" value={`${idea.probability.toFixed(1)}%`} />
                <Metric label="EV / $100" value={formatSignedDollars(idea.ev_per_100)} />
                <Metric label="Quarter Kelly" value={`${(idea.quarter_kelly * 100).toFixed(1)}%`} />
              </div>
              {idea.note ? <p className="mt-3 text-sm leading-6 text-slate-400">{idea.note}</p> : null}
            </div>
          ))
        ) : (
          <div className="rounded-md border border-slate-800 bg-slate-950 px-4 py-5 text-sm text-slate-500">
            No saved bet ideas yet. Open a game and save a thesis from the Bet Idea Notebook panel.
          </div>
        )}
      </div>
    </section>
  );
}

function GameCard({
  game,
  watched = false,
  onSelect,
  onToggleWatch,
}: {
  game: GameSummary;
  watched?: boolean;
  onSelect: (id: string) => void;
  onToggleWatch?: (id: string) => void;
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(game.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(game.id);
        }
      }}
      className="w-full cursor-pointer rounded-md border border-slate-800 bg-slate-900/80 p-4 text-left transition hover:border-cyan-500/70 hover:bg-slate-900"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
            <Clock className="h-3.5 w-3.5" />
            {formatTime(game.commence_time)}
          </div>
          <h2 className="mt-2 text-lg font-semibold text-slate-50">
            {game.away_team.abbreviation} at {game.home_team.abbreviation}
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            {game.away_team.name} at {game.home_team.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onToggleWatch ? (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onToggleWatch(game.id);
              }}
              className={`rounded-md border p-2 ${watched ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-200" : "border-slate-700 text-slate-400 hover:border-cyan-400/50 hover:text-cyan-200"}`}
              aria-label={watched ? "Remove from watchlist" : "Add to watchlist"}
            >
              <Star className="h-4 w-4" />
            </button>
          ) : null}
          <div className="rounded-md border border-cyan-400/30 bg-cyan-400/10 px-2.5 py-1 text-xs font-semibold text-cyan-200">
            Opportunity {game.opportunity_score.toFixed(0)}
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        <Metric label="Current Spread" value={spreadText(game)} />
        <Metric label="Open" value={openingSpreadText(game)} />
        <Metric label="Moneyline" value={moneylineText(game)} />
        <Metric label="Total" value={totalText(game)} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {game.opportunity_reasons.slice(0, 2).map((reason) => (
          <span
            key={`${game.id}-${reason}`}
            className="rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-xs font-medium text-cyan-100"
          >
            {reason}
          </span>
        ))}
        {marketRegimes(game).slice(0, 3).map((regime) => (
          <span
            key={`${game.id}-${regime}`}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs font-medium text-slate-300"
          >
            {regime}
          </span>
        ))}
        {game.signals.slice(0, 3).map((signal) => (
          <span
            key={`${game.id}-${signal.signal_type}`}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs font-medium text-slate-300"
          >
            {signal.signal_type}
          </span>
        ))}
      </div>
    </div>
  );
}

function chartSelection(detail: GameDetail, mode: ChartMode) {
  if (mode === "total") return "Over";
  return detail.home_team.name;
}

function chartValue(row: OddsHistoryPoint, mode: ChartMode) {
  if (mode === "moneyline") return row.odds_american;
  return row.line;
}

function buildChartData(detail: GameDetail, mode: ChartMode) {
  const marketType: MarketType = mode === "home_spread" ? "spread" : mode;
  const selection = chartSelection(detail, mode);
  const rows = detail.odds_history.filter((row) => row.market_type === marketType && row.selection === selection);
  const timestamps = Array.from(new Set(rows.map((row) => row.timestamp))).sort();

  return timestamps.map((timestamp) => {
    const point: Record<string, string | number | null> = {
      time: new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(timestamp)),
    };
    for (const row of rows.filter((item) => item.timestamp === timestamp)) {
      point[row.sportsbook] = chartValue(row, mode);
    }
    return point;
  });
}

function OddsTable({ rows }: { rows: OddsLine[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-800">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead className="bg-slate-950 text-left text-[11px] font-semibold uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Sportsbook</th>
            <th className="px-4 py-3">Market</th>
            <th className="px-4 py-3">Selection</th>
            <th className="px-4 py-3">Line</th>
            <th className="px-4 py-3">Odds</th>
            <th className="px-4 py-3">Implied</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800 bg-slate-900">
          {rows.map((line) => (
            <tr key={`${line.sportsbook}-${line.market_type}-${line.selection}-${line.line}-${line.odds_american}`}>
              <td className="px-4 py-3 font-semibold text-slate-100">{line.sportsbook}</td>
              <td className="px-4 py-3 capitalize text-slate-400">{line.market_type}</td>
              <td className="px-4 py-3 text-slate-300">{line.selection}</td>
              <td className="px-4 py-3 text-slate-300">{formatLine(line.line)}</td>
              <td className="px-4 py-3 text-slate-300">{formatOdds(line.odds_american)}</td>
              <td className="px-4 py-3 text-slate-300">{formatPercent(line.implied_probability)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GameDetailView({
  detail,
  context,
  watched,
  onBack,
  onToggleWatch,
  onSaveBetIdea,
}: {
  detail: GameDetail;
  context: GameContext | null;
  watched: boolean;
  onBack: () => void;
  onToggleWatch: (id: string) => void;
  onSaveBetIdea: (idea: SavedBetIdea) => void;
}) {
  const [chartMode, setChartMode] = useState<ChartMode>("home_spread");
  const activeChartMode = CHART_MODES.find((mode) => mode.key === chartMode) ?? CHART_MODES[0];
  const chartData = useMemo(() => buildChartData(detail, chartMode), [detail, chartMode]);
  const chartBooks = useMemo(
    () => Array.from(new Set(detail.odds_history.map((row) => row.sportsbook))).slice(0, BOOK_COLORS.length),
    [detail],
  );

  return (
    <section className="space-y-5">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm font-semibold text-slate-200 hover:border-cyan-500"
      >
        <ArrowLeft className="h-4 w-4" />
        Today&apos;s Board
      </button>

      <div className="rounded-md border border-slate-800 bg-slate-900 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase text-cyan-300">Game Detail</div>
            <h2 className="mt-2 text-2xl font-semibold text-slate-50">
              {detail.away_team.name} at {detail.home_team.name}
            </h2>
            <p className="mt-1 text-sm text-slate-400">{formatTime(detail.commence_time)} tipoff</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {marketRegimes(detail).map((regime) => (
                <span key={`${detail.id}-${regime}`} className="rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-xs font-semibold text-cyan-100">
                  {regime}
                </span>
              ))}
            </div>
          </div>
          <div className="grid gap-2 sm:grid-cols-4">
            <Metric label="Spread" value={spreadText(detail)} />
            <Metric label="Open" value={openingSpreadText(detail)} />
            <Metric label="Moneyline" value={moneylineText(detail)} />
            <Metric label="Total" value={totalText(detail)} />
          </div>
        </div>
        <button
          type="button"
          onClick={() => onToggleWatch(detail.id)}
          className={`mt-4 inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold ${
            watched ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-100" : "border-slate-700 text-slate-300 hover:border-cyan-400/50 hover:text-cyan-100"
          }`}
        >
          <Star className="h-4 w-4" />
          {watched ? "Watching" : "Add to Watchlist"}
        </button>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="h-80 rounded-md border border-slate-800 bg-slate-900 p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold uppercase text-slate-300">Line Movement Chart</h3>
            <div className="flex rounded-md border border-slate-800 bg-slate-950 p-1">
              {CHART_MODES.map((mode) => (
                <button
                  key={mode.key}
                  type="button"
                  onClick={() => setChartMode(mode.key)}
                  className={`rounded px-2.5 py-1 text-xs font-semibold transition ${
                    chartMode === mode.key ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:text-slate-100"
                  }`}
                  title={mode.description}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-500">{activeChartMode.description}</span>
          </div>
          <ResponsiveContainer width="100%" height="88%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155", color: "#e2e8f0" }} />
              {chartBooks.map((book, index) => (
                <Line key={book} type="monotone" dataKey={book} stroke={BOOK_COLORS[index]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <aside className="space-y-3">
          <h3 className="text-sm font-semibold uppercase text-slate-300">Market Signals</h3>
          {detail.signals.map((signal) => (
            <SignalBadge key={`${detail.id}-${signal.signal_type}`} signal={signal} />
          ))}
        </aside>
      </div>

      <QuantPanel detail={detail} />

      <MovementPanel alerts={detail.movement_alerts} />

      <BetIdeaPanel detail={detail} onSave={onSaveBetIdea} />

      <InjuryNewsPanel context={context} />

      <OddsTable rows={detail.book_table} />
    </section>
  );
}

function App() {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [detail, setDetail] = useState<GameDetail | null>(null);
  const [gameContext, setGameContext] = useState<GameContext | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("board");
  const [command, setCommand] = useState("");
  const [watchlist, setWatchlist] = useState<string[]>(() => readStoredJson<string[]>(WATCHLIST_STORAGE_KEY, []));
  const [betIdeas, setBetIdeas] = useState<SavedBetIdea[]>(() => readStoredJson<SavedBetIdea[]>(BET_IDEAS_STORAGE_KEY, []));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/games/today`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load today's board.");
        return response.json();
      })
      .then((data) => {
        setGames(data);
        setError(null);
      })
      .catch((caught: Error) => setError(caught.message));
  }, []);

  useEffect(() => {
    window.localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist));
  }, [watchlist]);

  useEffect(() => {
    window.localStorage.setItem(BET_IDEAS_STORAGE_KEY, JSON.stringify(betIdeas));
  }, [betIdeas]);

  useEffect(() => {
    if (!selectedGameId) {
      setDetail(null);
      setGameContext(null);
      return;
    }

    fetch(`${API_BASE}/games/${selectedGameId}`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load game detail.");
        return response.json();
      })
      .then((data) => {
        setDetail(data);
        setError(null);
      })
      .catch((caught: Error) => setError(caught.message));

    fetch(`${API_BASE}/context/mlb/games/${selectedGameId}`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load injury/news context.");
        return response.json();
      })
      .then((data) => {
        setGameContext(data);
        setError(null);
      })
      .catch((caught: Error) => setError(caught.message));
  }, [selectedGameId]);

  const signalCount = games.reduce((total, game) => total + game.signals.length, 0);
  const sportsbookCount = new Set(games.flatMap((game) => Object.values(game.current_markets).flat().map((line) => line.sportsbook))).size;
  const opportunityCount = games.filter((game) => game.opportunity_score > 0 || game.price_alerts.length > 0).length;

  function selectGame(id: string) {
    setSelectedGameId(id);
    setCommand("");
  }

  function toggleWatchlist(id: string) {
    setWatchlist((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  function saveBetIdea(idea: SavedBetIdea) {
    setBetIdeas((current) => [idea, ...current]);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-black px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-emerald-300">
              <Radio className="h-4 w-4" />
              Live MLB market feed
            </div>
            <h1 className="mt-1 text-xl font-semibold">Sports Market Terminal</h1>
          </div>
          <div className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300">
            The Odds API odds / SportsDataIO injuries
          </div>
        </div>
        <div className="mt-4 max-w-3xl">
          <CommandBar
            command={command}
            games={games}
            onCommandChange={setCommand}
            onSelectGame={selectGame}
            onSetView={(view) => {
              setViewMode(view);
              setSelectedGameId(null);
              setCommand("");
            }}
          />
        </div>
      </header>

      <div className="border-b border-slate-800 bg-slate-950 px-5 py-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Stat icon={<Activity className="h-4 w-4" />} label="MLB Games" value={String(games.length)} />
          <Stat icon={<AlertTriangle className="h-4 w-4" />} label="Active Signals" value={String(signalCount)} />
          <Stat icon={<Star className="h-4 w-4" />} label="Watchlist" value={String(watchlist.length)} />
          <Stat icon={<TrendingUp className="h-4 w-4" />} label="Opportunities" value={`${opportunityCount} / ${sportsbookCount} books`} />
        </div>
      </div>

      <div className="px-5 py-5">
        {error ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div> : null}
        {selectedGameId && detail ? (
          <GameDetailView
            detail={detail}
            context={gameContext}
            watched={watchlist.includes(detail.id)}
            onBack={() => setSelectedGameId(null)}
            onToggleWatch={toggleWatchlist}
            onSaveBetIdea={saveBetIdea}
          />
        ) : (
          <section className="space-y-4">
            <div className="flex rounded-md border border-slate-800 bg-slate-950 p-1 md:w-fit">
              {[
                ["board", "Board"],
                ["opportunities", "Opportunities"],
                ["watchlist", "Watchlist"],
                ["notebook", "Notebook"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setViewMode(key as ViewMode)}
                  className={`rounded px-3 py-1.5 text-sm font-semibold transition ${
                    viewMode === key ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:text-slate-100"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            {viewMode === "opportunities" ? (
              <OpportunityBoard games={games} onSelectGame={selectGame} />
            ) : viewMode === "watchlist" ? (
              <WatchlistBoard games={games} watchlist={watchlist} onSelectGame={selectGame} onToggleWatch={toggleWatchlist} />
            ) : viewMode === "notebook" ? (
              <NotebookView
                ideas={betIdeas}
                onDelete={(id) => setBetIdeas((current) => current.filter((idea) => idea.id !== id))}
                onSelectGame={selectGame}
              />
            ) : (
              <div className="grid gap-4">
                {games.map((game) => (
                  <GameCard
                    key={game.id}
                    game={game}
                    watched={watchlist.includes(game.id)}
                    onSelect={selectGame}
                    onToggleWatch={toggleWatchlist}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
