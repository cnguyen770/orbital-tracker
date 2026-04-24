import { useEffect, useState, useRef } from "react"
import { Viewer, Entity, PolylineGraphics } from "resium"
import { Cartesian3, Color, Ion } from "cesium"
import FeaturedPanel from "./FeaturedPanel"
import { NearMeButton, OverheadList } from "./NearMePanel"
Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2NGJhZDczOC0zYTc5LTRjZDktYjNkYi01MmUxMzQwN2Y1NGYiLCJpZCI6NDIxNzAyLCJpYXQiOjE3NzY4NDMyMzh9.OaICnFcsNYdu4DnFB4qm7yRjQusGmvoIstYPeVK568Y"

const API = "http://127.0.0.1:8000/api"

const GROUPS = ["stations", "weather", "starlink"]

const GROUP_COLORS = {
  stations: Color.CYAN,
  weather: Color.LIME,
  starlink: Color.ORANGE,
}

export default function App() {
  const [activeGroups, setActiveGroups] = useState(["stations"])
  const [satellites, setSatellites] = useState([])
  const [positions, setPositions] = useState({})
  const [selectedNorad, setSelectedNorad] = useState(null)
  const [orbitalPath, setOrbitalPath] = useState([])
  const [conjunctions, setConjunctions] = useState([])
  const viewerRef = useRef(null)
  const [userLocation, setUserLocation] = useState(null)
  const [overheadSats, setOverheadSats] = useState([])

  // Fetch satellite metadata whenever active groups change
  useEffect(() => {
    if (activeGroups.length === 0) {
      setSatellites([])
      return
    }

    const fetchSatellites = async () => {
      const results = await Promise.all(
        activeGroups.map(group =>
          fetch(`${API}/satellites/?group=${group}`)
            .then(r => r.json())
            .then(sats => sats.map(s => ({ ...s, group })))
            .catch(() => [])
        )
      )
      setSatellites(results.flat())
    }
    fetchSatellites()
  }, [activeGroups])

  // Fetch positions in a single batched call per group
  useEffect(() => {
    if (activeGroups.length === 0) {
      setPositions({})
      return
    }

    const fetchPositions = async () => {
      const results = await Promise.all(
        activeGroups.map(group =>
          fetch(`${API}/satellites/positions?group=${group}&limit=500`)
            .then(r => r.json())
            .catch(() => null)
        )
      )
      const posMap = {}
      results.forEach(batch => {
        if (!batch || !batch.positions) return
        batch.positions.forEach(pos => {
          posMap[pos.norad_id] = pos
        })
      })
      setPositions(posMap)
    }

    fetchPositions()
    const interval = setInterval(fetchPositions, 30000)
    return () => clearInterval(interval)
  }, [activeGroups])

  // Fetch orbital path for selected satellite
  useEffect(() => {
    if (!selectedNorad) {
      setOrbitalPath([])
      return
    }
    fetch(`${API}/satellites/${selectedNorad}/path?minutes=90`)
      .then(r => r.json())
      .then(data => setOrbitalPath(data.path || []))
  }, [selectedNorad])

  // Fetch conjunctions once on mount
  useEffect(() => {
    fetch(`${API}/satellites/conjunctions?group=weather&threshold_km=200&minutes=30`)
      .then(r => r.json())
      .then(data => setConjunctions(data.conjunctions || []))
  }, [])

  const toCartesian = (lat, lon, alt) =>
    Cartesian3.fromDegrees(lon, lat, alt * 1000)

  const pathPositions = orbitalPath.map(p =>
    toCartesian(p.latitude, p.longitude, p.altitude_km)
  )

  const toggleGroup = (group) => {
    setActiveGroups(prev =>
      prev.includes(group)
        ? prev.filter(g => g !== group)
        : [...prev, group]
    )
  }
const handleFeaturedSelect = async (noradId) => {
  // Make sure the satellite's group is loaded so it renders
  const res = await fetch(`${API}/satellites/${noradId}`)
  const sat = await res.json()
  if (sat.group && !activeGroups.includes(sat.group)) {
    setActiveGroups(prev => [...prev, sat.group])
  }

  setSelectedNorad(noradId)

  // Fly camera to the satellite (needs current position)
  const posRes = await fetch(`${API}/satellites/${noradId}/position`)
  const pos = await posRes.json()

  if (viewerRef.current?.cesiumElement && pos.latitude !== undefined) {
    const { Cartesian3 } = await import("cesium")
    viewerRef.current.cesiumElement.camera.flyTo({
      destination: Cartesian3.fromDegrees(
        pos.longitude,
        pos.latitude,
        pos.altitude_km * 1000 + 2_000_000  // 2000km above the satellite for context
      ),
      duration: 2.0,
    })
  }
}
  const selectedSat = satellites.find(s => s.norad_id === selectedNorad)
  const selectedPos = positions[selectedNorad]
  const selectedConjunctions = conjunctions.filter(
    c => c.norad_id_a === selectedNorad || c.norad_id_b === selectedNorad
  )
  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", background: "#000" }}>
      <Viewer
        ref={viewerRef}
        full
        timeline={false}
        animation={false}
        homeButton={false}
        sceneModePicker={false}
        navigationHelpButton={false}
        geocoder={false}
        baseLayerPicker={false}
        fullscreenButton={false}
      >
        {satellites.map(sat => {
          const pos = positions[sat.norad_id]
          if (!pos) return null
          const color = GROUP_COLORS[sat.group] || Color.WHITE
          const isSelected = sat.norad_id === selectedNorad
          return (
            <Entity
              key={sat.norad_id}
              position={toCartesian(pos.latitude, pos.longitude, pos.altitude_km)}
              point={{ pixelSize: isSelected ? 10 : 4, color }}
              label={isSelected ? {
                text: sat.name,
                font: "12px sans-serif",
                fillColor: Color.WHITE,
                showBackground: true,
                backgroundColor: Color.BLACK.withAlpha(0.7),
                pixelOffset: { x: 0, y: -20 },
              } : undefined}
              onClick={() => setSelectedNorad(sat.norad_id)}
            />
          )
        })}

        {userLocation && (
          <Entity
            position={toCartesian(userLocation.lat, userLocation.lon, 0)}
            point={{ pixelSize: 12, color: Color.YELLOW }}
            label={{
              text: "YOU",
              font: "12px sans-serif",
              fillColor: Color.YELLOW,
              showBackground: true,
              backgroundColor: Color.BLACK.withAlpha(0.7),
              pixelOffset: { x: 0, y: -24 },
            }}
          />
        )}

        {pathPositions.length > 1 && (
          <Entity>
            <PolylineGraphics
              positions={pathPositions}
              width={2}
              material={Color.YELLOW.withAlpha(0.8)}
            />
          </Entity>
        )}
      </Viewer>
      <FeaturedPanel onSelect={handleFeaturedSelect} />
      <div style={{
        position: "absolute",
        top: 20,
        left: 20,
        display: "flex",
        gap: 8,
        fontFamily: "monospace",
      }}>
        {GROUPS.map(group => {
          const active = activeGroups.includes(group)
          return (
            <button
              key={group}
              onClick={() => toggleGroup(group)}
              style={{
                padding: "8px 14px",
                borderRadius: 4,
                border: `2px solid ${active ? "#fff" : "#444"}`,
                background: active
                  ? GROUP_COLORS[group].toCssColorString()
                  : "rgba(0,0,0,0.6)",
                color: active ? "#000" : "#888",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              {group}
            </button>
          )
        })}
        <NearMeButton
          userLocation={userLocation}
          overheadSats={overheadSats}
          onLocationSet={setUserLocation}
          onOverheadFound={setOverheadSats}
        />
      </div>

      <OverheadList
        userLocation={userLocation}
        overheadSats={overheadSats}
        onSelect={setSelectedNorad}
      />

      {selectedSat && selectedPos && (
        <div style={{
          position: "absolute",
          bottom: userLocation ? 340 : 20,
          left: 20,
          background: "rgba(0,0,0,0.85)",
          color: "white",
          padding: 16,
          borderRadius: 8,
          fontFamily: "monospace",
          fontSize: 12,
          border: `1px solid ${GROUP_COLORS[selectedSat.group]?.toCssColorString() || "#fff"}`,
          minWidth: 240,
          maxWidth: 320,
        }}>
          <div style={{ color: "#00ccff", fontWeight: "bold", marginBottom: 4 }}>
            {selectedSat.name}
          </div>
          <div style={{ color: "#888", marginBottom: 8, textTransform: "uppercase" }}>
            {selectedSat.group}
          </div>
          <div>LAT: {selectedPos.latitude.toFixed(2)}°</div>
          <div>LON: {selectedPos.longitude.toFixed(2)}°</div>
          <div>ALT: {selectedPos.altitude_km.toFixed(1)} km</div>
          <div>SPD: {selectedPos.speed_km_s.toFixed(3)} km/s</div>

          {selectedConjunctions.length > 0 && (
            <div style={{ marginTop: 12, paddingTop: 10, borderTop: "1px solid #333" }}>
              <div style={{ color: "#ff4444", fontWeight: "bold", marginBottom: 6 }}>
                ⚠ CONJUNCTIONS ({selectedConjunctions.length})
              </div>
              {selectedConjunctions.map((c, i) => {
                const other = c.norad_id_a === selectedNorad ? c.satellite_b : c.satellite_a
                return (
                  <div key={i} style={{ marginBottom: 4, fontSize: 11 }}>
                    <div style={{ color: "#ffaa00" }}>{other}</div>
                    <div style={{ color: "#888" }}>
                      Closest: {c.closest_approach_km.toFixed(1)} km
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          <div
            style={{ color: "#ff4444", cursor: "pointer", marginTop: 12 }}
            onClick={() => setSelectedNorad(null)}
          >
            ✕ close
          </div>
        </div>
      )}
    </div>
  )
}