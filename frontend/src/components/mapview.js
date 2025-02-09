import React from "react";
import { MapContainer, TileLayer, Marker } from "react-leaflet";

function MapView() {
  return (
    <MapContainer center={[37.7749, -122.4194]} zoom={10} style={{ height: "400px", width: "100%" }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Marker position={[37.7749, -122.4194]} />
    </MapContainer>
  );
}

export default MapView;
