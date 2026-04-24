import { Component } from "react"

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error("Rendering error:", error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          width: "100vw",
          height: "100vh",
          background: "#000",
          color: "#fff",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "monospace",
          padding: 24,
          textAlign: "center",
        }}>
          <div style={{ color: "#ff4444", fontSize: 20, marginBottom: 16 }}>
            ⚠ Rendering error
          </div>
          <div style={{ color: "#aaa", maxWidth: 500, marginBottom: 24, fontSize: 14 }}>
            Something went wrong rendering the 3D globe.
            This is usually a transient WebGL or network issue.
          </div>
          <div style={{ color: "#666", fontSize: 12, marginBottom: 24, maxWidth: 500 }}>
            {this.state.error?.message || "Unknown error"}
          </div>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "10px 20px",
              background: "#00ccff",
              color: "#000",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontWeight: "bold",
              fontFamily: "monospace",
            }}
          >
            RELOAD
          </button>
        </div>
      )
    }
    return this.props.children
  }
}