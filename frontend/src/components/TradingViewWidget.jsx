// TradingViewWidget.jsx
import React, { useEffect, useRef, memo } from "react";

function TradingViewWidget({ symbol = "OANDA:XAUUSD", interval = "60" }) {
  const container = useRef(null);

  useEffect(() => {
    if (!container.current) return;

    container.current.innerHTML = "";

    const script = document.createElement("script");

    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";

    script.type = "text/javascript";
    script.async = true;

    script.innerHTML = JSON.stringify({
      allow_symbol_change: false,
      calendar: false,
      details: false,
      hide_side_toolbar: true,
      hide_top_toolbar: false,
      hide_legend: false,
      hide_volume: true,
      hotlist: false,
      interval,
      locale: "en",
      save_image: true,
      style: "1",
      symbol,
      theme: "dark",
      timezone: "Etc/UTC",
      backgroundColor: "#0F0F0F",
      gridColor: "rgba(242, 242, 242, 0.08)",
      watchlist: [],
      withdateranges: true,
      compareSymbols: [],
      support_host: "https://www.tradingview.com",
      studies: [],
      autosize: true
    });

    container.current.appendChild(script);

    return () => {
      if (container.current) {
        container.current.innerHTML = "";
      }
    };
  }, [symbol, interval]);

  return (
    <div
      className="tradingview-widget-container"
      ref={container}
      style={{
        height: "100%",
        width: "100%"
      }}
    >
      <div
        className="tradingview-widget-container__widget"
        style={{
          height: "100%",
          width: "100%"
        }}
      />
    </div>
  );
}

export default memo(TradingViewWidget);