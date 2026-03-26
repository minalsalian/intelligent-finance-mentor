import axios from "axios";
import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from "recharts";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

function Dashboard() {

  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");

  const [health, setHealth] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [expenseData, setExpenseData] = useState([]);
  const [collapsed, setCollapsed] = useState(false);
  const [animatedScore, setAnimatedScore] = useState(0);

  const COLORS = ["#3b82f6", "#22d3ee", "#8b5cf6", "#f59e0b", "#ef4444"];

  // Fetch Data
  useEffect(() => {
    if (!userId) {
      navigate("/");
      return;
    }

    axios.get(`http://127.0.0.1:8000/health/score/${userId}`)
      .then(res => setHealth(res.data));

    axios.get(`http://127.0.0.1:8000/health/recommendations/${userId}`)
      .then(res => setRecommendations(res.data));

    axios.get(`http://127.0.0.1:8000/expenses/summary/${userId}`)
      .then(res => {
        const formatted = res.data.summary.map(item => ({
          name: item.category,
          value: item.total
        }));
        setExpenseData(formatted);
      });

  }, [userId, navigate]);

  // Animated Score
  useEffect(() => {
    if (!health) return;

    let start = 0;
    const end = health.overall_financial_health_score;
    const duration = 1000;
    const increment = end / (duration / 16);

    const counter = setInterval(() => {
      start += increment;
      if (start >= end) {
        start = end;
        clearInterval(counter);
      }
      setAnimatedScore(Math.floor(start));
    }, 16);

  }, [health]);

  const getScoreColor = (score) => {
    if (score >= 80) return "#10b981";
    if (score >= 50) return "#f59e0b";
    return "#ef4444";
  };

  const handleLogout = () => {
    localStorage.removeItem("user_id");
    navigate("/");
  };

  const cardStyle = {
    background: "rgba(255,255,255,0.04)",
    backdropFilter: "blur(20px)",
    borderRadius: "20px",
    border: "1px solid rgba(255,255,255,0.08)",
    boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
    padding: "28px"
  };

  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      fontFamily: "Inter, sans-serif",
      background: `
        radial-gradient(circle at 20% 20%, rgba(59,130,246,0.15), transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(34,211,238,0.1), transparent 40%),
        #0f172a
      `
    }}>


      {/* MAIN CONTENT */}
      <div style={{ flex: 1, padding: "40px", color: "white" }}>

        {health && recommendations ? (
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{
              hidden: {},
              visible: { transition: { staggerChildren: 0.2 } }
            }}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "40px"
            }}
          >

            {/* SCORE */}
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 30 },
                visible: { opacity: 1, y: 0 }
              }}
              whileHover={{ y: -5 }}
              style={cardStyle}
            >
              <h3 style={{ marginBottom: "20px" }}>Financial Health Score</h3>

              <div style={{ width: "180px" }}>
                <CircularProgressbar
                  value={animatedScore}
                  text={`${animatedScore}`}
                  styles={buildStyles({
                    textColor: "#fff",
                    pathColor: getScoreColor(animatedScore),
                    trailColor: "#1e293b"
                  })}
                />
              </div>
            </motion.div>

            {/* AI RECOMMENDATIONS */}
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 30 },
                visible: { opacity: 1, y: 0 }
              }}
              whileHover={{ y: -5 }}
              style={cardStyle}
            >
              <h3 style={{ marginBottom: "15px" }}>AI Recommendations</h3>
              <p style={{ color: "#22d3ee", marginBottom: "10px" }}>
                {recommendations.priority_level}
              </p>
              <ul>
                {recommendations.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </motion.div>

            {/* EXPENSE BREAKDOWN */}
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 30 },
                visible: { opacity: 1, y: 0 }
              }}
              whileHover={{ y: -5 }}
              style={cardStyle}
            >
              <h3 style={{ marginBottom: "20px" }}>Expense Breakdown</h3>

              {expenseData.length > 0 && (
                <PieChart width={350} height={280}>
                  <Pie
                    data={expenseData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={60}
                    outerRadius={100}
                  >
                    {expenseData.map((entry, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              )}
            </motion.div>

            {/* FINANCIAL OVERVIEW */}
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 30 },
                visible: { opacity: 1, y: 0 }
              }}
              whileHover={{ y: -5 }}
              style={cardStyle}
            >
              <h3 style={{ marginBottom: "15px" }}>Financial Overview</h3>
              <p>Income: ₹{health.income}</p>
              <p>Expenses: ₹{health.total_expenses}</p>
              <p>Savings: ₹{health.savings}</p>
              <p>Savings Rate: {(health.savings_rate * 100).toFixed(1)}%</p>
            </motion.div>

          </motion.div>
        ) : (
          <p style={{ color: "#94a3b8" }}>Loading financial insights...</p>
        )}

      </div>
    </div>
  );
}

export default Dashboard;
