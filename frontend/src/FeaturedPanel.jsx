import { useState, useEffect } from "react"

const API = "http://127.0.0.1:8000/api"

export default function FeaturedPanel({ onSelect }) {
  const [featured, setFeatured] = useState([])
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    fetch(`${API}/satellites/featured`)
      .then(r => r.json())
      .then(data => setFeatured(data.satellites || []))
      .catch(() => setFeatured([]))
  }, [])

  return (
    <div style={{
      position: "absolute",
      bottom: 20,
      right: 20,
      width: collapsed ? 40 : 280,
      background: "rgba(0,0,0,0.85)",
      color: "white",
      borderRadius: 8,
      fontFamily: "monospace",
      fontSize: 12,
      border: "1px solid #333",
      transition: "width 0.2s",
      maxHeight: "80vh",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
    }}>
      <div
        onClick={() => setCollapsed(!collapsed)}
        style={{
          padding: "10px 14px",
          borderBottom: collapsed ? "none" : "1px solid #333",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          fontWeight: "bold",
          color: "#00ccff",
          userSelect: "none",
        }}
      >
        {collapsed ? "★" : (
          <>
            <span>★ FEATURED</span>
            <span style={{ color: "#666" }}>{featured.length}</span>
          </>
        )}
      </div>

      {!collapsed && (
        <div style={{ overflowY: "auto", padding: "4px 0" }}>
          {featured.map(sat => (
            <div
              key={sat.norad_id}
              onClick={() => sat.available && onSelect(sat.norad_id)}
              style={{
                padding: "10px 14px",
                borderBottom: "1px solid #222",
                cursor: sat.available ? "pointer" : "not-allowed",
                opacity: sat.available ? 1 : 0.4,
                transition: "background 0.15s",
              }}
              onMouseEnter={e => {
                if (sat.available) e.currentTarget.style.background = "rgba(0,204,255,0.1)"
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = "transparent"
              }}
            >
              <div style={{ color: "#00ccff", fontWeight: "bold", marginBottom: 2 }}>
                {sat.tagline}
              </div>
              <div style={{ color: "#888", fontSize: 11, marginBottom: 4 }}>
                {sat.description}
              </div>
              <div style={{ color: "#555", fontSize: 10, textTransform: "uppercase" }}>
                {sat.available
                  ? `${sat.group} • NORAD ${sat.norad_id}`
                  : "not yet ingested"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}