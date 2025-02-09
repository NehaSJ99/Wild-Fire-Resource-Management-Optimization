import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import MapView from "./components/MapView";
import Navbar from "./components/Navbar"; 
import OptimizedResources from "./components/OptimizedResources";
import PredictSpread from "./components/PredictSpread";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/map" element={<MapView />} />
        <Route path="/optimize_resources" element={<OptimizedResources />} />
        <Route path="/predict_results" element={<PredictSpread />} />
      </Routes>
    </Router>
  );
}

export default App;
