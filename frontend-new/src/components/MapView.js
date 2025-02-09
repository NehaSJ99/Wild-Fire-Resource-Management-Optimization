import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const MapView = () => {
  return (
    <div style={{ height: "90vh", width: "100%" }}>
      <MapContainer center={[37.7749, -122.4194]} zoom={6} style={{ height: "100%", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Marker position={[37.7749, -122.4194]}>
          <Popup>🔥 Wildfire Alert: San Francisco</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

export default MapView;
