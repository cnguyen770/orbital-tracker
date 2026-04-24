import { useState } from "react"

const API = "http://127.0.0.1:8000/api"

export function NearMeButton({ onLocationSet, onOverheadFound, userLocation }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const findNearMe = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.")
      return
    }

    setLoading(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        onLocationSet({ lat: latitude, lon: longitude })

        try {
          const res = await fetch(
            `${API}/satellites/overhead?lat=${latitude}&lon=${longitude}&radius_km=1000`
          )
          const data = await res.json()
          onOverheadFound(data.satellites || [])
        } catch (e) {
          setError("Failed to fetch overhead satellites.")
        } finally {
          setLoading(false)
        }
      },
      (err) => {
        setError(
          err.code === 1
            ? "Location permission denied."
            : "Could not get your location."
        )
        setLoading(false)
      },
      { timeout: 10000, maximumAge: 60000 }
    )
  }

  return (
    <button
      onClick={findNearMe}
      disabled={loading}
      style={{
        padding: "8px 14px",
        borderRadius: 4,
        border: `2px solid ${userLocation ? "#ffcc00" : "#444"}`,
        background: userLocation ? "rgba(255, 204, 0, 0.15)" : "rgba(0,0,0,0.6)",
        color: userLocation ? "#ffcc00" : "#aaa",
        cursor: loading ? "wait" : "pointer",
        fontSize: 12,
        fontWeight: "bold",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        fontFamily: "monospace",
      }}
      title={error || undefined}
    >
      {loading ? "..." : userLocation ? "📍 LOCATED" : "📍 NEAR ME"}
    </button>
  )
}

export function OverheadList({ userLocation, overheadSats, onSelect }) {
  if (!userLocation || !overheadSats || overheadSats.length === 0) return null

  return (
    <div style={{
      position: "absolute",
      bottom: 20,
      left: 20,
      background: "rgba(0,0,0,0.85)",
      color: "white",
      padding: 16,
      borderRadius: 8,
      width: 300,
      maxHeight: "calc(100vh - 40px)",
      overflowY: "auto",
      fontFamily: "monospace",
      fontSize: 12,
      border: "1px solid #ffcc00",
      boxSizing: "border-box",
    }}>
      <div style={{ color: "#ffcc00", fontWeight: "bold", marginBottom: 8 }}>
        📍 OVERHEAD ({overheadSats.length})
      </div>
      <div style={{ color: "#666", fontSize: 10, marginBottom: 10 }}>
        {userLocation.lat.toFixed(2)}°, {userLocation.lon.toFixed(2)}° • 1000 km radius
      </div>
      {overheadSats.map(sat => (
        <div
          key={sat.norad_id}
          onClick={() => onSelect(sat.norad_id)}
          style={{
            marginBottom: 8,
            padding: 6,
            borderRadius: 4,
            cursor: "pointer",
            borderBottom: "1px solid #222",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "rgba(255,204,0,0.1)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          <div style={{ color: "#fff" }}>{sat.name}</div>
          <div style={{ color: "#888", fontSize: 11 }}>
            {sat.distance_km.toFixed(0)} km away • {sat.altitude_km.toFixed(0)} km up
          </div>
        </div>
      ))}
    </div>
  )
}