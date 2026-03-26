import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { createChart } from "lightweight-charts";

function TradingMentor() {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);

  const userId = localStorage.getItem("user_id");

  const [symbol, setSymbol] = useState("AAPL");
  const [loading, setLoading] = useState(false);
  const [candles, setCandles] = useState([]);
  const [quantity, setQuantity] = useState(1);

  const [trades, setTrades] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [equityHistory, setEquityHistory] = useState([]);

  const [aiPrediction, setAiPrediction] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);

  const currentPrice =
    candles.length > 0 && !isNaN(candles[candles.length - 1].close)
      ? Number(candles[candles.length - 1].close)
      : 0;

  useEffect(() => {
    if (!chartContainerRef.current || chartRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 450,
      layout: {
        background: { color: "#0f172a" },
        textColor: "#d1d5db",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    seriesRef.current = candleSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`http://127.0.0.1:8000/market/candles/${symbol}`);
      const data = res.data.candles || [];
      setCandles(data);

      if (seriesRef.current) {
        seriesRef.current.setData(data);
      }
    } catch (err) {
      alert("Failed to fetch market data");
    } finally {
      setLoading(false);
    }
  };

  const fetchAIPrediction = async () => {
    try {
      setLoadingAI(true);

      const predRes = await axios.get(`http://127.0.0.1:8000/mentor/predict/${symbol}`);
      setAiPrediction(predRes.data);

      const analysisRes = await axios.get(`http://127.0.0.1:8000/mentor/analysis/${symbol}`);
      setAiAnalysis(analysisRes.data);
    } catch (err) {
      console.error("AI prediction error:", err);
      alert("Failed to get AI prediction");
    } finally {
      setLoadingAI(false);
    }
  };

  const fetchTrades = async () => {
    try {
      if (!userId) {
        setTrades([]);
        return;
      }

      const res = await axios.get(`http://127.0.0.1:8000/trades/${userId}`);

      let tradeArray = [];
      if (Array.isArray(res.data)) {
        tradeArray = res.data;
      } else if (res.data.trades && Array.isArray(res.data.trades)) {
        tradeArray = res.data.trades;
      }

      setTrades(tradeArray);
    } catch (error) {
      console.error("Trade fetch error:", error);
      setTrades([]);
    }
  };

  const fetchPortfolio = async () => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/portfolio/${userId}`);
      setPortfolio(res.data);
    } catch (err) {
      console.log("Portfolio fetch error");
    }
  };

  const fetchEquityHistory = async () => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/portfolio/history/${userId}`);
      setEquityHistory(res.data.history || []);
    } catch (err) {
      console.log("Equity history error");
    }
  };

  useEffect(() => {
    if (!userId) return;
    fetchTrades();
    fetchPortfolio();
    fetchEquityHistory();
  }, [userId]);

  const buy = async () => {
    if (!currentPrice) {
      alert("Load market data first");
      return;
    }

    try {
      await axios.post(`http://127.0.0.1:8000/trades/${userId}`, {
        symbol,
        type: "BUY",
        price: currentPrice,
        quantity,
      });

      fetchTrades();
      fetchPortfolio();
      fetchEquityHistory();
    } catch (err) {
      console.log("Buy error");
    }
  };

  const sell = async () => {
    if (!currentPrice) {
      alert("Load market data first");
      return;
    }

    try {
      await axios.post(`http://127.0.0.1:8000/trades/${userId}`, {
        symbol,
        type: "SELL",
        price: currentPrice,
        quantity,
      });

      fetchTrades();
      fetchPortfolio();
      fetchEquityHistory();
    } catch (err) {
      console.log("Sell error");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "40px",
        background: "#0f172a",
        color: "white",
      }}
    >
      <h2>📈 Trading Mentor</h2>

      <div style={{ marginBottom: "20px", display: "flex", gap: "10px", alignItems: "center" }}>
        <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        <button onClick={fetchData}>{loading ? "Loading..." : "Load"}</button>
        <button onClick={fetchAIPrediction} disabled={loadingAI}>
          {loadingAI ? "🤖 Analyzing..." : "🤖 Get AI Prediction"}
        </button>
      </div>

      {aiPrediction && (
        <div
          style={{
            background: "#1e293b",
            padding: "16px",
            borderRadius: "12px",
            marginBottom: "20px",
          }}
        >
          <h3>🔮 AI Prediction</h3>
          <p>
            <strong>Direction:</strong> {aiPrediction.prediction}
          </p>
          <p>
            <strong>Probability Up:</strong> {aiPrediction.probability_up}%
          </p>
          <p>
            <strong>Probability Down:</strong> {aiPrediction.probability_down}%
          </p>
          <p>
            <strong>Confidence:</strong> {aiPrediction.confidence_level}
          </p>
          <p style={{ fontSize: "12px", opacity: 0.8 }}>{aiPrediction.disclaimer}</p>
        </div>
      )}

      {aiAnalysis && (
        <div
          style={{
            background: "#1e293b",
            padding: "16px",
            borderRadius: "12px",
            marginBottom: "20px",
          }}
        >
          <h3>🧠 AI Analysis</h3>
          <p>
            <strong>Bullish Signals:</strong> {aiAnalysis.signals_bullish}
          </p>
          <ul>
            {(aiAnalysis.technical_analysis || []).map((signal, idx) => (
              <li key={idx}>
                <strong>{signal.indicator}:</strong> {signal.status} — {signal.interpretation}
              </li>
            ))}
          </ul>
          <p style={{ whiteSpace: "pre-line" }}>{aiAnalysis.recommendation}</p>
        </div>
      )}

      <div
        ref={chartContainerRef}
        style={{ width: "100%", height: "450px", marginBottom: "30px" }}
      />

      {portfolio && (
        <div
          style={{
            background: "#1e293b",
            padding: "20px",
            borderRadius: "12px",
            marginBottom: "30px",
          }}
        >
          <h3>Portfolio Summary</h3>
          <p>Total Invested: ₹{Number(portfolio.total_invested || 0).toFixed(2)}</p>
          <p style={{ color: portfolio.unrealized_pnl >= 0 ? "#22c55e" : "#ef4444" }}>
            Unrealized P&L: ₹{Number(portfolio.unrealized_pnl || 0).toFixed(2)}
          </p>
          <p>Net Equity: ₹{Number(portfolio.net_equity || 0).toFixed(2)}</p>
        </div>
      )}

      <div style={{ marginBottom: "30px" }}>
        <h3>Trade</h3>
        <input
          type="number"
          value={quantity}
          min="1"
          onChange={(e) => setQuantity(Number(e.target.value))}
        />
        <button onClick={buy}>Buy</button>
        <button onClick={sell}>Sell</button>
      </div>

      <div
        style={{
          background: "#1e293b",
          padding: "20px",
          borderRadius: "12px",
          marginTop: "30px",
        }}
      >
        <h3>Trade History</h3>

        {trades.length === 0 ? (
          <p>No trades yet</p>
        ) : (
          <table style={{ width: "100%", marginTop: "15px", textAlign: "center" }}>
            <thead>
              <tr>
                <th>Type</th>
                <th>Buy Price</th>
                <th>Current</th>
                <th>Qty</th>
                <th>Unrealized P&L</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id}>
                  <td style={{ color: trade.type === "BUY" ? "#22c55e" : "#ef4444" }}>
                    {trade.type}
                  </td>
                  <td>₹{Number(trade.entry_price).toFixed(2)}</td>
                  <td>₹{Number(trade.current_price).toFixed(2)}</td>
                  <td>{trade.quantity}</td>
                  <td style={{ color: trade.unrealized_pnl >= 0 ? "#22c55e" : "#ef4444" }}>
                    ₹{Number(trade.unrealized_pnl).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div style={{ marginTop: "30px" }}>
        <h3>Equity History</h3>
        {equityHistory.length === 0 ? (
          <p>No history yet</p>
        ) : (
          <ul>
            {equityHistory.map((item, index) => (
              <li key={index}>
                {(item.time || item.date)} → ₹{item.equity}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default TradingMentor;