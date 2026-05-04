import MapView from './components/MapView.jsx';

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">TerraGalicia DSS</p>
          <h1>Interactive parcel map</h1>
          <p className="subtitle">
            SIGPAC-first parcel loading with automatic local fallback, rendered with React and Leaflet.
          </p>
        </div>
        <div className="header-chip">Resilient data mode</div>
      </header>
      <main className="map-frame">
        <MapView />
      </main>
    </div>
  );
}