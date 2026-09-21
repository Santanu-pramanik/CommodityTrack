import React, { useEffect, useState } from "react";
import "./App.css";

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

function MiniLine({ silver = false }) {
  const points = silver
    ? "0,50 10,45 20,49 30,40 40,37 50,42 60,30 70,32 80,24 90,29 100,20 110,25 120,13 130,18 140,8 150,18"
    : "0,50 10,43 20,49 30,31 40,38 50,21 60,32 70,24 80,28 90,14 100,25 110,18 120,7 130,17 140,4 150,14";
  return (
    <svg viewBox="0 0 150 55" className="mini-line" preserveAspectRatio="none">
      <defs>
        <linearGradient id={silver ? "sg" : "gg"} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00d49a" stopOpacity=".25"/>
          <stop offset="100%" stopColor="#00d49a" stopOpacity="0"/>
        </linearGradient>
      </defs>
      <polyline points={points} fill="none" stroke="#00e6a8" strokeWidth="2.4" />
      <polygon points={`${points} 150,55 0,55`} fill={`url(#${silver ? "sg" : "gg"})`} />
    </svg>
  );
}

function CandleChart({ silver = false }) {
  const bars = [
    [8,34,20],[20,30,28],[32,26,36],[44,31,41],[56,22,34],[68,24,44],[80,18,37],
    [92,28,49],[104,16,30],[116,20,42],[128,11,31],[140,14,26],[152,10,27],[164,13,35],
    [176,7,20],[188,16,34],[200,12,29],[212,9,24],[224,14,31],[236,18,37],[248,12,26],
    [260,10,22],[272,15,29],[284,9,22],[296,14,28],[308,8,19],[320,13,23],[332,10,21],
    [344,7,18],[356,14,27]
  ];
  return (
    <svg viewBox="0 0 390 135" className="candle-chart" preserveAspectRatio="none">
      {[15,45,75,105].map((y) => (<line key={y} x1="0" y1={y} x2="390" y2={y} className="grid"/>))}
      {[35,80,125,170,215,260,305,350].map((x) => (<line key={x} x1={x} y1="0" x2={x} y2="120" className="grid"/>))}
      {bars.map(([x, top, bottom], i) => {
        const up = (i + (silver ? 1 : 0)) % 4 !== 0;
        const bodyTop = Math.min(top + 7, bottom - 6);
        const bodyBottom = Math.max(top + 12, bottom - 2);
        return (
          <g key={i}>
            <line x1={x+3} y1={top} x2={x+3} y2={bottom} stroke={up ? "#10d8a2" : "#ff4962"} strokeWidth="1.4"/>
            <rect x={x} y={bodyTop} width="6" height={Math.max(5, bodyBottom-bodyTop)} rx="1"
              fill={up ? "#10d8a2" : "#ff4962"} />
          </g>
        );
      })}
      <line x1="0" y1="120" x2="390" y2="120" className="axis"/>
      {["00:00", "06:00", "12:00", "18:00"].map((t, i) => (
        <text key={t} x={i * 118 + 4} y="133" className="axis-text">{t}</text>
      ))}
      {[silver ? "53.0" : "4,380", silver ? "52.5" : "4,360", silver ? "52.0" : "4,340", silver ? "51.5" : "4,320"].map((t, i) => (
        <text key={t} x="364" y={16+i*29} className="axis-text">{t}</text>
      ))}
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

function Sidebar() {
  const [dashboardOpen, setDashboardOpen] = React.useState(true);
  const [activeMenu, setActiveMenu] = React.useState("Home");

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

          // Gold / Silver
          if (cls === "sub" && !dashboardOpen) {
            return null;
          }

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
                  setDashboardOpen(!dashboardOpen);
                } else {
                  setActiveMenu(label);
                }
              }}
            >
              <Icon>{ico}</Icon>

              <span>{label}</span>

              {label === "Market Dashboard" && (
                <em className={dashboardOpen ? "arrow-open" : ""}>
                  ⌄
                </em>
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

function AssetCard({ silver = false }) {
  return (
    <div className="asset-card">
      <div className={`metal-icon ${silver ? "silver-metal" : ""}`}>{silver ? "▰" : "▰"}</div>
      <div className="asset-copy">
        <div className="asset-name">{silver ? "Silver (XAG/USD)" : "Gold (XAU/USD)"}</div>
        <div className="asset-price">{silver ? "$52.31" : "$4,356.82"}</div>
        <div className="asset-change">+{silver ? "0.82 (+1.59%)" : "18.46 (+0.43%)"}</div>
      </div>
      <MiniLine silver={silver}/>
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
    const fetchEvents = async () => {
      try {
        setLoading(true);
        setError("");

        console.log(`Fetching events for ${days} days...`);

        const response = await fetch(
          `https://commoditytrack-production-5160.up.railway.app/api/events/upcoming?days=${days}`
        );

        console.log("API response:", response.status);

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();

        console.log("Economic events:", data);

        setEvents(data.events || []);
      } catch (err) {
        console.error("Economic calendar error:", err);
        setError(err.message || "Unable to load economic events.");
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [days]);

  const formatDate = (dateString) => {
    if (!dateString) return "—";

    const date = new Date(`${dateString}T00:00:00`);

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (eventTime) => {
    if (!eventTime) return "—";

    const date = new Date(eventTime);

    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) {
      return "—";
    }

    return value;
  };

  const formatImpact = (impact) => {
    if (!impact) return "Neutral";

    return (
      impact.charAt(0).toUpperCase() +
      impact.slice(1).toLowerCase()
    );
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
            setDays(days === 7 ? 30 : 7);
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

            {loading && (
              <tr>
                <td colSpan="9" style={{ textAlign: "center" }}>
                  Loading economic events...
                </td>
              </tr>
            )}

            {!loading && error && (
              <tr>
                <td
                  colSpan="9"
                  style={{
                    textAlign: "center",
                    color: "#ff4962",
                  }}
                >
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

            {!loading &&
              !error &&
              events.map((event) => (
                <tr key={event.id}>

                  <td>{formatDate(event.date)}</td>

                  <td>{formatTime(event.event_time)}</td>

                  <td>
                    <strong>{event.event}</strong>
                  </td>

                  <td>{formatValue(event.previous)}</td>

                  <td>{formatValue(event.forecast)}</td>

                  <td>{formatValue(event.actual)}</td>

                  <td>
                    <Badge type={formatImpact(event.impact)}>
                      {formatImpact(event.impact)}
                    </Badge>
                  </td>

                  <td>
                    <Badge type={event.gold_effect}>
                      {event.gold_effect || "Neutral"}
                    </Badge>
                  </td>

                  <td>
                    <Badge type={event.silver_effect}>
                      {event.silver_effect || "Neutral"}
                    </Badge>
                  </td>

                </tr>
              ))}

          </tbody>

        </table>

      </div>

    </section>
  );
}

function MarketOverview() {
  return (
    <section className="panel market-panel">
      <div className="panel-head">
        <div className="section-title">
          ▥ <span>Market Overview</span>
        </div>

        <div className="market-tabs">
          <button className="selected">Gold</button>
          <button>Silver</button>
          <button className="selected soft">1D</button>
          <button>1W</button>
          <button>1M</button>
          <button>3M</button>
        </div>
      </div>

      <div className="chart-grid">
        {[false, true].map((silver) => (
          <div
            className="chart-card"
            key={silver ? "silver" : "gold"}
          >
            <div className="chart-top">
              <div>
                <div className="chart-name">
                  {silver ? "Silver (XAG/USD)" : "Gold (XAU/USD)"}
                </div>

                <strong>
                  {silver ? "$52.31" : "$4,356.82"}
                </strong>

                <span>
                  +{silver ? "1.59%" : "0.43%"}
                </span>
              </div>
            </div>

            <CandleChart silver={silver} />
          </div>
        ))}
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

export default function App() {
  return (
    <div className="app-shell">
      <Topbar/>
      <Sidebar/>
      <main className="main">
        <div className="left-column">
          <div className="asset-row">
            <AssetCard/>
            <AssetCard silver/>
            <ReportsCard/>
          </div>
          <Calendar/>
          <MarketOverview/>
          <div className="bottom-grid">
            <NewsPanel/>
            <SpeechPanel/>
          </div>
        </div>
        <div className="right-column">
          <AIPrediction/>
          <Sentiment/>
        </div>
      </main>
    </div>
  );
}
