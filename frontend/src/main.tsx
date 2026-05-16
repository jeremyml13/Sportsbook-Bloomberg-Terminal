import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { Activity, AlertTriangle, ArrowLeft, ArrowRightLeft, Clock, Radio, TrendingUp } from "lucide-react";
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
};

type GameDetail = GameSummary & {
  odds_history: OddsHistoryPoint[];
  book_table: OddsLine[];
};

const API_BASE = "http://127.0.0.1:8000";
const BOOK_COLORS: Record<string, string> = {
  DraftKings: "#22c55e",
  FanDuel: "#38bdf8",
  BetMGM: "#f59e0b",
  Caesars: "#a78bfa",
};

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

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

function firstLine(markets: OddsLine[], sportsbook = "DraftKings") {
  return markets.find((line) => line.sportsbook === sportsbook) ?? markets[0];
}

function moneylineText(game: GameSummary) {
  const home = game.current_markets.moneyline.find(
    (line) => line.sportsbook === "DraftKings" && line.selection === game.home_team.name,
  );
  const away = game.current_markets.moneyline.find(
    (line) => line.sportsbook === "DraftKings" && line.selection === game.away_team.name,
  );
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

function GameCard({ game, onSelect }: { game: GameSummary; onSelect: (id: string) => void }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(game.id)}
      className="w-full rounded-md border border-slate-800 bg-slate-900/80 p-4 text-left transition hover:border-cyan-500/70 hover:bg-slate-900"
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
        <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-300">
          {game.signals.length} signals
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        <Metric label="Current Spread" value={spreadText(game)} />
        <Metric label="Open" value={openingSpreadText(game)} />
        <Metric label="Moneyline" value={moneylineText(game)} />
        <Metric label="Total" value={totalText(game)} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {game.signals.slice(0, 3).map((signal) => (
          <span
            key={`${game.id}-${signal.signal_type}`}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs font-medium text-slate-300"
          >
            {signal.signal_type}
          </span>
        ))}
      </div>
    </button>
  );
}

function buildChartData(detail: GameDetail) {
  const spreadRows = detail.odds_history.filter(
    (row) => row.market_type === "spread" && row.selection === detail.home_team.name,
  );
  const timestamps = Array.from(new Set(spreadRows.map((row) => row.timestamp))).sort();

  return timestamps.map((timestamp) => {
    const point: Record<string, string | number | null> = {
      time: new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(timestamp)),
    };
    for (const row of spreadRows.filter((item) => item.timestamp === timestamp)) {
      point[row.sportsbook] = row.line;
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

function GameDetailView({ detail, onBack }: { detail: GameDetail; onBack: () => void }) {
  const chartData = useMemo(() => buildChartData(detail), [detail]);

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
          </div>
          <div className="grid gap-2 sm:grid-cols-4">
            <Metric label="Spread" value={spreadText(detail)} />
            <Metric label="Open" value={openingSpreadText(detail)} />
            <Metric label="Moneyline" value={moneylineText(detail)} />
            <Metric label="Total" value={totalText(detail)} />
          </div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="h-80 rounded-md border border-slate-800 bg-slate-900 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase text-slate-300">Line Movement Chart</h3>
            <span className="text-xs text-slate-500">Home spread by sportsbook</span>
          </div>
          <ResponsiveContainer width="100%" height="88%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155", color: "#e2e8f0" }} />
              {Object.entries(BOOK_COLORS).map(([book, color]) => (
                <Line key={book} type="monotone" dataKey={book} stroke={color} strokeWidth={2} dot={false} />
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

      <OddsTable rows={detail.book_table} />
    </section>
  );
}

function App() {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [detail, setDetail] = useState<GameDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/games/today`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load today's board.");
        return response.json();
      })
      .then(setGames)
      .catch((caught: Error) => setError(caught.message));
  }, []);

  useEffect(() => {
    if (!selectedGameId) {
      setDetail(null);
      return;
    }

    fetch(`${API_BASE}/games/${selectedGameId}`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load game detail.");
        return response.json();
      })
      .then(setDetail)
      .catch((caught: Error) => setError(caught.message));
  }, [selectedGameId]);

  const signalCount = games.reduce((total, game) => total + game.signals.length, 0);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-black px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-emerald-300">
              <Radio className="h-4 w-4" />
              Mock NBA market feed
            </div>
            <h1 className="mt-1 text-xl font-semibold">Sports Market Terminal</h1>
          </div>
          <div className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300">
            DraftKings / FanDuel / BetMGM / Caesars
          </div>
        </div>
      </header>

      <div className="border-b border-slate-800 bg-slate-950 px-5 py-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Stat icon={<Activity className="h-4 w-4" />} label="NBA Games" value={String(games.length)} />
          <Stat icon={<AlertTriangle className="h-4 w-4" />} label="Active Signals" value={String(signalCount)} />
          <Stat icon={<ArrowRightLeft className="h-4 w-4" />} label="Sportsbooks" value="4" />
          <Stat icon={<TrendingUp className="h-4 w-4" />} label="Markets" value="Spread / ML / Total" />
        </div>
      </div>

      <div className="px-5 py-5">
        {error ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div> : null}
        {selectedGameId && detail ? (
          <GameDetailView detail={detail} onBack={() => setSelectedGameId(null)} />
        ) : (
          <div className="grid gap-4">
            {games.map((game) => (
              <GameCard key={game.id} game={game} onSelect={setSelectedGameId} />
            ))}
          </div>
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
