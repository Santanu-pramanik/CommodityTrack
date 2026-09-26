import React, {
  useEffect,
  useState,
  useContext,
  createContext,
} from "react";
import "./App.css";
import TradingViewWidget from "./components/TradingViewWidget";
import LoginPage from "./components/LoginPage";
import NotificationPreference from "./components/NotificationPreference";

import {
  getUserIdFromURL,
  isLoginSuccess,
} from "./services/auth";
// Railway Backend Production API URL
const API_BASE = "https://commoditytrack-production-5160.up.railway.app";
const MarketContext = createContext(null);

const news = [
  ["🏛️", "US CPI inflation remains elevated, keeps Fed rate cut hopes alive", "2 hours ago", "Reuters", "Positive", "Gold ↑", "Silver ↑"],
  ["🏭", "Geopolitical tensions in Middle East increase safe-haven demand", "4 hours ago", "Bloomberg", "Positive", "Gold ↑", "Silver ↑"],
  ["🏛️", "Fed officials signal cautious approach on rate cuts", "6 hours ago", "CNBC", "Negative", "Gold ↓", "Silver ↓"],
  ["💵", "Strong dollar weighs on precious metals", "8 hours ago", "MarketWatch", "Negative", "Gold ↓", "Silver ↓"],
];

const speeches = [
  {
    avatar: "👤",
    name: "Donald Trump",
    role: "Former U.S. President",
    date: "Sep 14, 2026 • 8:15 PM (ET)",
    quote: "We may consider new tariffs on certain imports to protect American industries...",
    tags: ["Gold ↑", "Silver ↑", "USD ↓", "Oil ↑"],
  },
  {
    avatar: "👨‍💼",
    name: "Jerome Powell",
    role: "Fed Chair",
    date: "Sep 12, 2026 • 2:30 PM (ET)",
    quote: "We need to see more progress on inflation before adjusting rates...",
    tags: ["Gold ↓", "Silver ↓", "USD ↑", "Yield ↑"],
  },
];

function getTodayFormatted() {
  return new Date().toLocaleDateString("en-US", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function Icon({ children }) {
  return <span className="icon">{children}</span>;
}

function MiniLine({ data = [] }) {
  if (!data || data.length < 2) {
    return (
      <svg
        viewBox="0 0 150 55"
        className="mini-line"
        preserveAspectRatio="none"
      />
    );
  }

  const prices = data.map((item) => Number(item.price));
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  const points = prices
    .map((price, index) => {
      const x = (index / (prices.length - 1)) * 150;
      const y = 50 - ((price - min) / range) * 40;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 150 55" className="mini-line" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke="#00e6a8"
        strokeWidth="2.4"
      />
    </svg>
  );
}

function CandleChart({ data = [], silver = false }) {
  const width = 390;
  const height = 135;
  const chartTop = 6;
  const chartBottom = 120;

  const candles = (Array.isArray(data) ? data : [])
    .map((item) => ({
      timestamp: item.timestamp,
      open: Number(item.open),
      high: Number(item.high),
      low: Number(item.low),
      close: Number(item.close),
    }))
    .filter(
      (item) =>
        Number.isFinite(item.open) &&
        Number.isFinite(item.high) &&
        Number.isFinite(item.low) &&
        Number.isFinite(item.close)
    );

  if (candles.length === 0) {
    return (
      <svg
        viewBox="0 0 390 135"
        className="candle-chart"
        preserveAspectRatio="none"
      >
        {[15, 45, 75, 105].map((y) => (
          <line
            key={y}
            x1="0"
            y1={y}
            x2="390"
            y2={y}
            className="grid"
          />
        ))}
        <line x1="0" y1="120" x2="390" y2="120" className="axis" />
        <text x="145" y="70" className="axis-text">
          No candle data
        </text>
      </svg>
    );
  }

  const minPrice = Math.min(...candles.map((c) => c.low));
  const maxPrice = Math.max(...candles.map((c) => c.high));
  const range = maxPrice - minPrice || 1;

  const y = (price) =>
    chartBottom -
    ((price - minPrice) / range) * (chartBottom - chartTop);

  const slot = width / candles.length;
  const bodyWidth = Math.max(2, Math.min(8, slot * 0.55));

  return (
    <svg
      viewBox="0 0 390 135"
      className="candle-chart"
      preserveAspectRatio="none"
    >
      {[15, 45, 75, 105].map((lineY) => (
        <line
          key={lineY}
          x1="0"
          y1={lineY}
          x2="390"
          y2={lineY}
          className="grid"
        />
      ))}

      {candles.map((candle, index) => {
        const x = index * slot + slot / 2;
        const openY = y(candle.open);
        const closeY = y(candle.close);
        const highY = y(candle.high);
        const lowY = y(candle.low);
        const up = candle.close >= candle.open;
        const bodyY = Math.min(openY, closeY);
        const bodyHeight = Math.max(1.5, Math.abs(closeY - openY));

        return (
          <g key={`${candle.timestamp}-${index}`}>
            <line
              x1={x}
              y1={highY}
              x2={x}
              y2={lowY}
              stroke={up ? "#10d8a2" : "#ff4962"}
              strokeWidth="1.4"
            />
            <rect
              x={x - bodyWidth / 2}
              y={bodyY}
              width={bodyWidth}
              height={bodyHeight}
              rx="1"
              fill={up ? "#10d8a2" : "#ff4962"}
            />
          </g>
        );
      })}

      <line x1="0" y1="120" x2="390" y2="120" className="axis" />

      {["00:00", "06:00", "12:00", "18:00"].map((t, i) => (
        <text key={t} x={i * 118 + 4} y="133" className="axis-text">
          {t}
        </text>
      ))}

      <text x="350" y="16" className="axis-text">
        {maxPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}
      </text>

      <text x="350" y="113" className="axis-text">
        {minPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}
      </text>
    </svg>
  );
}

function Badge({ children, type = "" }) {
  return <span className={`badge ${type.toLowerCase().replace(/\s+/g, "-")}`}>{children}</span>;
}

function Topbar() {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">↗</div>
        <div>
          <div className="brand-title">Gold &amp; Silver</div>
          <div className="brand-subtitle">Market Intelligence</div>
        </div>
      </div>

      <div className="search">
        <span>⌕</span>
        <input placeholder="Search reports, events, or assets..." />
      </div>

      <div className="top-actions">
        <div className="date-box">
          ▣
          <span>
            {getTodayFormatted()}
            <br />
            <small>(Today)</small>
          </span>
        </div>

        <div className="bell">
          ♧<b>3</b>
        </div>

        <div className="user">
          <div className="avatar">S</div>
          <div>
            <strong>Santanu</strong>
            <small>Free Plan</small>
          </div>
          <span>⌄</span>
        </div>
      </div>
    </header>
  );
}

function Sidebar({ activeMenu, setActiveMenu }) {
  const [dashboardOpen, setDashboardOpen] = useState(true);

  const menuItems = [
    ["⌂", "Home"],
    ["▣", "Economic Calendar"],
    ["▰", "Market Dashboard"],
    ["◆", "Gold", "sub"],
    ["◈", "Silver", "sub"],
    ["▤", "News"],
    ["♩", "Speeches & Statements"],
    ["▥", "Event Analysis"],
    ["◔", "Historical Analysis"],
    ["⚙", "AI Prediction"],
    ["✿", "Settings"],
  ];

  return (
    <aside className="sidebar">
      <div className="nav-group">
        {menuItems.map(([ico, label, cls], i) => {
          if (cls === "sub" && !dashboardOpen) return null;

          return (
            <div
              key={i}
              className={`nav-item ${
                activeMenu === label ? "active" : ""
              } ${cls || ""} ${
                label === "Market Dashboard" ? "with-arrow" : ""
              }`}
              onClick={() => {
                if (label === "Market Dashboard") {
                  setDashboardOpen((prev) => !prev);
                  setActiveMenu("Market Dashboard");
                } else {
                  setActiveMenu(label);
                }
              }}
            >
              <Icon>{ico}</Icon>
              <span>{label}</span>
              {label === "Market Dashboard" && (
                <em className={dashboardOpen ? "arrow-open" : ""}>⌄</em>
              )}
            </div>
          );
        })}
      </div>

      <div className="quote-card">
        <div>
          “The best time to prepare for the market is before the event.”
        </div>
        <div className="quote-mark">↗</div>
      </div>
    </aside>
  );
}

function AssetCard({ silver = false, market, history }) {
  const price = Number(market?.price || 0);

  const change =
    market?.change_percent !== null &&
    market?.change_percent !== undefined
      ? Number(market.change_percent)
      : null;

  return (
    <div className="asset-card">
      <div className={`metal-icon ${silver ? "silver-metal" : ""}`}>
        ▰
      </div>

      <div className="asset-copy">
        <div className="asset-name">
          {silver ? "Silver (XAG/USD)" : "Gold (XAU/USD)"}
        </div>

        <div className="asset-price">
          {price > 0
            ? `$${price.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`
            : "—"}
        </div>

        <div
          className="asset-change"
          style={{
            color:
              change === null
                ? "#9aa4b2"
                : change >= 0
                ? "#00e6a8"
                : "#ff4962",
          }}
        >
          {change === null
            ? "—"
            : `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`}
        </div>
      </div>

      <MiniLine data={history} />
    </div>
  );
}

function ReportsCard() {
  return (
    <div className="reports-card">
      <div className="section-title">▣ <span>Upcoming Major Reports</span></div>
      <div className="reports-big">Next in 2 days</div>
      <div className="report-name">FOMC Meeting Minutes</div>
      <div className="report-time">Wed, 17 Sep 2026 &nbsp;|&nbsp; 2:00 PM (ET)</div>
    </div>
  );
}

function Calendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [days, setDays] = useState(7);

  useEffect(() => {
    let cancelled = false;

    const fetchEvents = async () => {
      try {
        setError("");

        const response = await fetch(
          `${API_BASE}/api/events/upcoming?days=${days}`,
          { cache: "no-store" }
        );

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        const allEvents = Array.isArray(data.events) ? data.events : [];

        const now = new Date();
        const endDate = new Date(now);
        endDate.setDate(endDate.getDate() + days);

        const filteredEvents = allEvents
          .filter((event) => {
            if (!event.event_time) return false;
            const eventDate = new Date(event.event_time);

            return (
              !Number.isNaN(eventDate.getTime()) &&
              eventDate >= now &&
              eventDate <= endDate
            );
          })
          .sort(
            (a, b) =>
              new Date(a.event_time) - new Date(b.event_time)
          );

        if (!cancelled) {
          setEvents(filteredEvents);
        }
      } catch (err) {
        console.error("Economic calendar error:", err);

        if (!cancelled) {
          setError(err.message || "Unable to load economic events.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchEvents();

    return () => {
      cancelled = true;
    };
  }, [days]);

  const formatDate = (dateValue, eventTime) => {
    const value = dateValue || eventTime;
    if (!value) return "—";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (eventTime) => {
    if (!eventTime) return "—";

    const date = new Date(eventTime);
    if (Number.isNaN(date.getTime())) return "—";

    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatValue = (value) => {
    if (value === null || value === undefined || value === "") return "—";
    return value;
  };

  const formatImpact = (impact) => {
    if (!impact) return "Neutral";
    const value = String(impact);
    return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
  };

  return (
    <section className="panel calendar-panel">
      <div className="panel-head">
        <div className="section-title">
          ▣ <span>Economic Calendar</span>
        </div>

        <div className="tabs">
          <button className="selected">
            {days === 7 ? "Next 7 Days" : "Next 30 Days"}
          </button>
        </div>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setDays((prev) => (prev === 7 ? 30 : 7));
          }}
        >
          {days === 7 ? "View All →" : "View 7 Days →"}
        </a>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Event / Report</th>
              <th>Previous</th>
              <th>Forecast</th>
              <th>Actual</th>
              <th>Impact</th>
              <th>Gold</th>
              <th>Silver</th>
            </tr>
          </thead>

          <tbody>
            {loading && events.length === 0 && (
              <tr>
                <td colSpan="9" style={{ textAlign: "center" }}>
                  Loading economic events...
                </td>
              </tr>
            )}

            {!loading && error && events.length === 0 && (
              <tr>
                <td colSpan="9" style={{ textAlign: "center", color: "#ff4962" }}>
                  {error}
                </td>
              </tr>
            )}

            {!loading && !error && events.length === 0 && (
              <tr>
                <td colSpan="9" style={{ textAlign: "center" }}>
                  No upcoming economic events.
                </td>
              </tr>
            )}

            {events.map((event) => {
              const eventName =
                event.event ??
                event.event_name ??
                event.name ??
                "Unknown Event";

              const previous =
                event.previous ??
                event.previous_value ??
                event.prior;

              const forecast =
                event.forecast ??
                event.forecast_value ??
                event.consensus;

              const actual =
                event.actual ??
                event.actual_value;

              const impact =
                event.impact ??
                event.importance ??
                "Neutral";

              const gold =
                event.gold_effect ??
                event.gold_impact ??
                "Neutral";

              const silver =
                event.silver_effect ??
                event.silver_impact ??
                "Neutral";

              return (
                <tr key={event.id ?? `${eventName}-${event.event_time}`}>
                  <td>{formatDate(event.date, event.event_time)}</td>
                  <td>{formatTime(event.event_time)}</td>
                  <td><strong>{eventName}</strong></td>
                  <td>{formatValue(previous)}</td>
                  <td>{formatValue(forecast)}</td>
                  <td>{formatValue(actual)}</td>
                  <td>
                    <Badge type={formatImpact(impact)}>
                      {formatImpact(impact)}
                    </Badge>
                  </td>
                  <td>
                    <Badge type={gold}>{gold || "Neutral"}</Badge>
                  </td>
                  <td>
                    <Badge type={silver}>{silver || "Neutral"}</Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function MarketOverview() {
  const { marketData } = useContext(MarketContext);

  const [selectedMetal, setSelectedMetal] = useState("all");
  const [selectedRange, setSelectedRange] = useState("1D");

  const rangeConfig = {
    "1D": "60",
    "1W": "240",
    "1M": "D",
    "3M": "D",
  };

  const cards =
    selectedMetal === "all"
      ? [false, true]
      : [selectedMetal === "silver"];

  const getPrice = (silver) => {
    const market = marketData?.[silver ? "silver" : "gold"];

    if (!market?.price) return "—";

    return `$${Number(market.price).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const getChange = (silver) => {
    const market = marketData?.[silver ? "silver" : "gold"];

    if (
      market?.change_percent === null ||
      market?.change_percent === undefined
    ) {
      return "—";
    }

    const value = Number(market.change_percent);

    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  return (
    <section className="panel market-panel">
      <div className="panel-head">

        <div className="section-title">
          ▥ <span>Market Overview</span>
        </div>

        <div className="market-tabs">

          <button
            className={selectedMetal === "gold" ? "selected" : ""}
            onClick={() => setSelectedMetal("gold")}
          >
            Gold
          </button>

          <button
            className={selectedMetal === "silver" ? "selected" : ""}
            onClick={() => setSelectedMetal("silver")}
          >
            Silver
          </button>

          <button
            className={selectedMetal === "all" ? "selected" : ""}
            onClick={() => setSelectedMetal("all")}
          >
            Both
          </button>

          {Object.keys(rangeConfig).map((range) => (
            <button
              key={range}
              className={
                selectedRange === range
                  ? "selected soft"
                  : ""
              }
              onClick={() => setSelectedRange(range)}
            >
              {range}
            </button>
          ))}

        </div>
      </div>

      <div className="chart-grid">

        {cards.map((silver) => {
          const metal = silver ? "silver" : "gold";
          const market = marketData?.[metal];

          return (
            <div
              className="chart-card"
              key={metal}
            >

              <div className="chart-top">

                <div>

                  <div className="chart-name">
                    {silver
                      ? "Silver (XAG/USD)"
                      : "Gold (XAU/USD)"}
                  </div>

                  <strong>
                    {getPrice(silver)}
                  </strong>

                  <span
                    style={{
                      color:
                        Number(market?.change_percent || 0) >= 0
                          ? "#10d8a2"
                          : "#ff4962",
                    }}
                  >
                    {getChange(silver)}
                  </span>

                </div>

              </div>

              <div
                style={{
                  width: "100%",
                  height: "380px",
                  marginTop: "15px",
                  borderRadius: "10px",
                  overflow: "hidden",
                }}
              >
                <TradingViewWidget
                  symbol={
                    silver
                      ? "OANDA:XAGUSD"
                      : "OANDA:XAUUSD"
                  }
                  interval={rangeConfig[selectedRange]}
                />
              </div>

            </div>
          );
        })}

      </div>
    </section>
  );
}

function NewsPanel() {
  return (
    <section className="panel bottom-panel">
      <div className="panel-head compact">
        <div className="section-title">▤ <span>Latest Gold &amp; Silver News</span></div>
        <a>View All →</a>
      </div>
      <div className="news-list">
        {news.map((n, i) => (
          <div className="news-row" key={i}>
            <div className="news-thumb">{n[0]}</div>
            <div className="news-main">
              <div>{n[1]}</div>
              <small>{n[2]} • {n[3]}</small>
            </div>
            <Badge type={n[4]}>{n[4]}</Badge>
            <span className="tiny-tag">{n[5]}</span>
            <span className="tiny-tag">{n[6]}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function SpeechPanel() {
  return (
    <section className="panel bottom-panel">
      <div className="panel-head compact">
        <div className="section-title">◌ <span>Recent Speeches &amp; Statements</span></div>
        <a>View All →</a>
      </div>
      <div className="speech-list">
        {speeches.map((s, i) => (
          <div className="speech-row" key={i}>
            <div className="speaker-avatar">{s.avatar}</div>
            <div className="speech-main">
              <strong>{s.name}</strong>
              <small>{s.role}<br/>{s.date}</small>
              <p>“{s.quote}”</p>
              <div className="impact">Key Impact &nbsp; {s.tags.map((t, j) => <span key={j} className="tiny-tag">{t}</span>)}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function PredictionCard({ silver=false }) {
  return (
    <div className="prediction-card">
      <div className="prediction-asset">
        <div className={`metal-icon ${silver ? "silver-metal" : ""}`}>▰</div>
        <strong>{silver ? "Silver (XAG/USD)" : "Gold (XAU/USD)"}</strong>
        <Badge type="up">⬆ UP</Badge>
      </div>
      <div className="prediction-metrics">
        <div><strong>{silver ? "71%" : "78%"}</strong><small>Probability</small></div>
        <div><strong>+{silver ? "0.7% to +1.5%" : "0.5% to +1.2%"}</strong><small>Expected Move</small></div>
        <div><strong>Next 1 hour</strong><small>Time Horizon</small></div>
      </div>
      <div className="factors">
        <b>Key Factors</b>
        {(silver
          ? ["Industrial demand outlook", "USD weakness", "Positive sentiment", "Historical CPI reaction"]
          : ["CPI higher than expected (inflation support)", "USD weakening", "Falling Treasury yields", "Positive market sentiment", "Historical reaction to similar CPI events"]
        ).map((x, i) => <div key={i}>✓ <span>{x}</span></div>)}
      </div>
      {silver && <button className="detail-button">View Detailed Analysis →</button>}
    </div>
  );
}

function AIPrediction() {
  return (
    <section className="right-panel">
      <div className="ai-head">
        <div><span className="spark">✣</span> AI Prediction</div><span className="live">Live</span>
      </div>
      <div className="ai-sub">Based on: &nbsp;Latest data + Historical patterns + Market sentiment</div>
      <PredictionCard/>
      <PredictionCard silver/>
    </section>
  );
}

function Sentiment() {
  return (
    <section className="right-panel sentiment">
      <div className="section-title">▥ <span>Quick Market Sentiment</span></div>
      <div className="sentiment-top">
        <div className="donut"><div><strong>62%</strong><span>Bullish</span></div></div>
        <div className="sentiment-bars">
          {[
            ["Bullish",62,"bull"],
            ["Bearish",22,"bear"],
            ["Neutral",16,"neutral"],
          ].map(([l,v,c]) => <div key={l}><span>{l}</span><div><i className={c} style={{width:`${v}%`}}></i></div><b>{v}%</b></div>)}
        </div>
      </div>
      <div className="influencers">
        <b>Top Influencing Factors</b>
        {[
          ["↑", "CPI & Inflation Data", "Bullish", "bullish"],
          ["↓", "Fed Policy Outlook", "Bearish", "bearish"],
          ["↑", "Geopolitical Tensions", "Bullish", "bullish"],
          ["↓", "USD Strength", "Bearish", "bearish"],
          ["↑", "Market Momentum", "Bullish", "bullish"],
        ].map((r,i)=><div key={i}><span className={r[3]}>{r[0]}</span><span>{r[1]}</span><em className={r[3]}>{r[2]}</em></div>)}
      </div>
    </section>
  );
}

function MarketProvider({ children }) {
  const [marketData, setMarketData] = useState({
    gold: null,
    silver: null,
  });

  const [historyData, setHistoryData] = useState({
    gold: [],
    silver: [],
  });

  const [marketLoading, setMarketLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchMarketData = async () => {
      try {
        const results = await Promise.allSettled([
          fetch(`${API_BASE}/api/market/gold`, {
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/market/silver`, {
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/market/history/gold?limit=30`, {
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/market/history/silver?limit=30`, {
            cache: "no-store",
          }),
        ]);

        if (cancelled) return;

        const [goldPrice, silverPrice, goldHistory, silverHistory] =
          results;

        if (
          goldPrice.status === "fulfilled" &&
          goldPrice.value.ok
        ) {
          const data = await goldPrice.value.json();

          setMarketData((prev) => ({
            ...prev,
            gold: data,
          }));
        }

        if (
          silverPrice.status === "fulfilled" &&
          silverPrice.value.ok
        ) {
          const data = await silverPrice.value.json();

          setMarketData((prev) => ({
            ...prev,
            silver: data,
          }));
        }

        if (
          goldHistory.status === "fulfilled" &&
          goldHistory.value.ok
        ) {
          const data = await goldHistory.value.json();

          setHistoryData((prev) => ({
            ...prev,
            gold: [...(data.data || [])].reverse(),
          }));
        }

        if (
          silverHistory.status === "fulfilled" &&
          silverHistory.value.ok
        ) {
          const data = await silverHistory.value.json();

          setHistoryData((prev) => ({
            ...prev,
            silver: [...(data.data || [])].reverse(),
          }));
        }

        setMarketLoading(false);
      } catch (error) {
        console.error("Market data error:", error);

        if (!cancelled) {
          setMarketLoading(false);
        }
      }
    };

    fetchMarketData();

    const interval = setInterval(fetchMarketData, 15000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <MarketContext.Provider
      value={{
        marketData,
        historyData,
        marketLoading,
      }}
    >
      {children}
    </MarketContext.Provider>
  );
}
function HomePage() {
  const { marketData, historyData } = useContext(MarketContext);

  return (
    <main className="main">
      <div className="left-column">
        <div className="asset-row">
          <AssetCard
            market={marketData.gold}
            history={historyData.gold}
          />
          <AssetCard
            silver
            market={marketData.silver}
            history={historyData.silver}
          />
          <ReportsCard />
        </div>

        <Calendar />
        <MarketOverview />

        <div className="bottom-grid">
          <NewsPanel />
          <SpeechPanel />
        </div>
      </div>

      <div className="right-column">
        <AIPrediction />
        <Sentiment />
      </div>
    </main>
  );
}

function ActivePage({ activeMenu }) {
  switch (activeMenu) {
    case "Economic Calendar":
      return (
        <main className="main">
          <div className="left-column">
            <Calendar />
          </div>
          <div className="right-column">
            <AIPrediction />
          </div>
        </main>
      );

    case "Market Dashboard":
      return <HomePage />;

    case "Gold":
      return (
        <main className="main">
          <div className="left-column">
            <MarketOverview />
          </div>
        </main>
      );

    case "Silver":
      return (
        <main className="main">
          <div className="left-column">
            <MarketOverview />
          </div>
        </main>
      );

    case "News":
      return (
        <main className="main">
          <div className="left-column">
            <NewsPanel />
          </div>
        </main>
      );

    case "Speeches & Statements":
      return (
        <main className="main">
          <div className="left-column">
            <SpeechPanel />
          </div>
        </main>
      );

    case "Event Analysis":
      return (
        <main className="main">
          <div className="left-column">
            <Calendar />
          </div>
        </main>
      );

    case "Historical Analysis":
      return (
        <main className="main">
          <div className="left-column">
            <MarketOverview />
          </div>
        </main>
      );

    case "AI Prediction":
      return (
        <main className="main">
          <div className="left-column">
            <AIPrediction />
          </div>
        </main>
      );

    case "Settings":
      return (
        <main className="main">
          <div className="left-column">
            <section className="panel">
              <div className="panel-head">
                <div className="section-title">
                  ⚙ <span>Settings</span>
                </div>
              </div>
            </section>
          </div>
        </main>
      );

    case "Home":
    default:
      return <HomePage />;
  }
}

export default function App() {
  const [activeMenu, setActiveMenu] = useState("Home");

  const [authState, setAuthState] = useState("checking");

  const [userId, setUserId] = useState(null);

  const [marketData, setMarketData] = useState({
    gold: null,
    silver: null,
  });

  const [historyData, setHistoryData] = useState({
    gold: [],
    silver: [],
  });

  /*
   * ================================
   * AUTH CHECK
   * ================================
   */
  useEffect(() => {
    const checkAuthentication = () => {
      try {
        // Check Google login callback
        const loggedIn = isLoginSuccess();
        const callbackUserId = getUserIdFromURL();

        if (loggedIn && callbackUserId) {
          console.log(
            "Google login successful. User ID:",
            callbackUserId
          );

          // Save user ID
          localStorage.setItem(
            "commoditytrack_user_id",
            String(callbackUserId)
          );

          setUserId(String(callbackUserId));

          // New Google login → notification preference
          setAuthState("notification");

          // Remove OAuth query parameters from URL
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname
          );

          return;
        }

        // Check previously logged-in user
        const savedUserId = localStorage.getItem(
          "commoditytrack_user_id"
        );

        if (savedUserId) {
          console.log(
            "Existing user found:",
            savedUserId
          );

          setUserId(savedUserId);
          setAuthState("dashboard");

          return;
        }

        // No user
        setAuthState("login");
      } catch (error) {
        console.error(
          "Authentication check failed:",
          error
        );

        setAuthState("login");
      }
    };

    checkAuthentication();
  }, []);

  /*
   * ================================
   * MARKET DATA
   * ================================
   */
  useEffect(() => {
    let cancelled = false;

    const fetchMarketData = async () => {
      try {
        const results = await Promise.allSettled([
          fetch(`${API_BASE}/api/market/gold`, {
            cache: "no-store",
          }),

          fetch(`${API_BASE}/api/market/silver`, {
            cache: "no-store",
          }),

          fetch(
            `${API_BASE}/api/market/history/gold?limit=30`,
            {
              cache: "no-store",
            }
          ),

          fetch(
            `${API_BASE}/api/market/history/silver?limit=30`,
            {
              cache: "no-store",
            }
          ),
        ]);

        if (cancelled) return;

        const [
          goldPrice,
          silverPrice,
          goldHistory,
          silverHistory,
        ] = results;

        // GOLD
        if (
          goldPrice.status === "fulfilled" &&
          goldPrice.value.ok
        ) {
          const data = await goldPrice.value.json();

          if (!cancelled) {
            setMarketData((prev) => ({
              ...prev,
              gold: data,
            }));
          }
        }

        // SILVER
        if (
          silverPrice.status === "fulfilled" &&
          silverPrice.value.ok
        ) {
          const data = await silverPrice.value.json();

          if (!cancelled) {
            setMarketData((prev) => ({
              ...prev,
              silver: data,
            }));
          }
        }

        // GOLD HISTORY
        if (
          goldHistory.status === "fulfilled" &&
          goldHistory.value.ok
        ) {
          const data =
            await goldHistory.value.json();

          if (!cancelled) {
            setHistoryData((prev) => ({
              ...prev,
              gold: Array.isArray(data.data)
                ? [...data.data].reverse()
                : [],
            }));
          }
        }

        // SILVER HISTORY
        if (
          silverHistory.status === "fulfilled" &&
          silverHistory.value.ok
        ) {
          const data =
            await silverHistory.value.json();

          if (!cancelled) {
            setHistoryData((prev) => ({
              ...prev,
              silver: Array.isArray(data.data)
                ? [...data.data].reverse()
                : [],
            }));
          }
        }
      } catch (error) {
        console.error(
          "Market data refresh error:",
          error
        );
      }
    };

    fetchMarketData();

    const interval = setInterval(
      fetchMarketData,
      15000
    );

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  /*
   * ================================
   * AUTH LOADING
   * ================================
   */
  if (authState === "checking") {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        Loading...
      </div>
    );
  }

  /*
   * ================================
   * LOGIN
   * ================================
   */
  if (authState === "login") {
    return (
      <div className="app-shell auth-preview">
        <Topbar />

        <Sidebar
          activeMenu={activeMenu}
          setActiveMenu={setActiveMenu}
        />

        <MarketContext.Provider
          value={{
            marketData,
            historyData,
          }}
        >
          <ActivePage
            activeMenu={activeMenu}
          />
        </MarketContext.Provider>

        <div className="login-overlay">
          <div className="login-modal">
            <LoginPage />
          </div>
        </div>
      </div>
    );
  }

  /*
   * ================================
   * NOTIFICATION PREFERENCE
   * ================================
   */
  if (authState === "notification") {
    return (
      <NotificationPreference
        userId={userId}
        onComplete={() => {
          console.log(
            "Notification preferences saved."
          );

          setAuthState("dashboard");
        }}
      />
    );
  }

  /*
   * ================================
   * DASHBOARD
   * ================================
   */
  return (
    <div className="app-shell">
      <Topbar />

      <Sidebar
        activeMenu={activeMenu}
        setActiveMenu={setActiveMenu}
      />

      <MarketContext.Provider
        value={{
          marketData,
          historyData,
        }}
      >
        <ActivePage
          activeMenu={activeMenu}
        />
      </MarketContext.Provider>
    </div>
  );
}