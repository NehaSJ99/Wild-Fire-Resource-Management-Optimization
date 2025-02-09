import React from "react";
import Dashboard from "./components/Dashboard";
import MapView from "./components/MapView";
import Alerts from "./components/Alerts";

function App() {
  return (
    <div className="App">
      <Dashboard />
      <MapView />
      <Alerts />
    </div>
  );
}

export default App;
