import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const MapView = () => {
  // Define a custom icon for the marker
  const customIcon = new L.Icon({
    iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
    iconSize: [25, 41], // Size of the icon
    iconAnchor: [12, 41], // Point of the icon that will correspond to marker's location
    popupAnchor: [1, -34], // Point from which the popup should open
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    shadowSize: [41, 41], // Size of the shadow
  });

  return (
    <div style={{ height: "90vh", width: "100%" }}>
      <MapContainer center={[37.7749, -122.4194]} zoom={6} style={{ height: "100%", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Marker position={[37.7749, -122.4194]} icon={customIcon}>
          <Popup>🔥 Wildfire Alert: San Francisco</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

export default MapView;
