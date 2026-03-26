import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";

function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("user_id");
    navigate("/");
  };

  const navItemStyle = (path) => ({
    marginBottom: "20px",
    padding: "12px",
    borderRadius: "10px",
    cursor: "pointer",
    background:
      location.pathname === path
        ? "linear-gradient(90deg,#3b82f6,#22d3ee)"
        : "transparent",
    transition: "0.2s"
  });

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

      {/* SIDEBAR */}
      <motion.div
        animate={{ width: collapsed ? 80 : 240 }}
        transition={{ duration: 0.3 }}
        style={{
          background: "rgba(255,255,255,0.03)",
          backdropFilter: "blur(15px)",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          color: "white"
        }}
      >
        <div>
          <div style={{
            display: "flex",
            justifyContent: collapsed ? "center" : "space-between",
            alignItems: "center",
            marginBottom: "40px"
          }}>
            {!collapsed && <h2 style={{ fontWeight: "600" }}>FinanceTwin</h2>}

            <button
              onClick={() => setCollapsed(!collapsed)}
              style={{
                background: "none",
                border: "none",
                color: "white",
                cursor: "pointer",
                fontSize: "18px"
              }}
            >
              ☰
            </button>
          </div>

          <motion.div
            whileHover={{ x: 4 }}
            style={navItemStyle("/dashboard")}
            onClick={() => navigate("/dashboard")}
          >
            📊 {!collapsed && "Dashboard"}
          </motion.div>

          <motion.div
            whileHover={{ x: 4 }}
            style={navItemStyle("/trading")}
            onClick={() => navigate("/trading")}
          >
            📈 {!collapsed && "Trading Mentor"}
          </motion.div>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          onClick={handleLogout}
          style={{
            padding: "12px",
            borderRadius: "12px",
            border: "none",
            background: "linear-gradient(90deg,#ef4444,#dc2626)",
            color: "white",
            cursor: "pointer",
            fontWeight: "500"
          }}
        >
          {!collapsed ? "Logout" : "🚪"}
        </motion.button>
      </motion.div>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, padding: "50px", color: "white" }}>
        <Outlet />
      </div>
    </div>
  );
}

export default Layout;
