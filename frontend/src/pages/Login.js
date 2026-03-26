import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

function Login({ setIsLoggedIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setLoading(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/login", {
        email: email,
        password: password
      });

      // Save user
      localStorage.setItem("user_id", res.data.user_id);

      // Update app state
      if (setIsLoggedIn) setIsLoggedIn(true);

      navigate("/dashboard");
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Login failed");
    }

    setLoading(false);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Inter, sans-serif",
        background: `
          radial-gradient(circle at 20% 20%, rgba(59,130,246,0.15), transparent 40%),
          radial-gradient(circle at 80% 80%, rgba(34,211,238,0.1), transparent 40%),
          #0f172a
        `
      }}
    >
      <motion.form
        onSubmit={handleLogin}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{
          width: "380px",
          padding: "40px",
          borderRadius: "24px",
          backdropFilter: "blur(25px)",
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          color: "white"
        }}
      >
        <h2 style={{ marginBottom: "10px" }}>FinanceTwin</h2>
        <p style={{ marginBottom: "30px", color: "#94a3b8" }}>
          Intelligent Personal Finance & Trading Mentor
        </p>

        {/* Email */}
        <input
          type="email"
          id="email"
          name="email"
          autoComplete="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={inputStyle}
        />

        {/* Password */}
        <input
          type="password"
          id="password"
          name="password"
          autoComplete="current-password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={inputStyle}
        />

        {errorMsg && (
          <p style={{ color: "#ef4444", marginBottom: "15px" }}>
            {errorMsg}
          </p>
        )}

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "14px",
            borderRadius: "14px",
            border: "none",
            fontSize: "15px",
            fontWeight: "600",
            cursor: "pointer",
            background: "linear-gradient(90deg,#3b82f6,#22d3ee)",
            color: "white",
            marginTop: "10px"
          }}
        >
          {loading ? "Logging in..." : "Login"}
        </motion.button>
      </motion.form>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "14px",
  marginBottom: "18px",
  borderRadius: "12px",
  border: "1px solid rgba(255,255,255,0.1)",
  background: "rgba(255,255,255,0.07)",
  color: "white",
  fontSize: "14px",
  outline: "none"
};

export default Login;
