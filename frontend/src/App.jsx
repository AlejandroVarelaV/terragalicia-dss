import MapView from './components/MapView.jsx';

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">TerraGalicia DSS</p>
          <h1>Mapa interactivo de parcelas</h1>
          <p className="subtitle">
            Visualización de parcelas agrícolas de Galicia.
          </p>
        </div>
      </header>
      <main className="map-frame">
        <MapView />
      </main>
    </div>
  );
}