import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const socket = io("http://localhost:5000");

function Alerts() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    socket.on("fire_alert", (alert) => {
      setAlerts((prev) => [...prev, alert]);
    });
  }, []);

  return (
    <div>
      <h2>Live Fire Alerts</h2>
      <ul>
        {alerts.map((alert, index) => (
          <li key={index}>{alert}</li>
        ))}
      </ul>
    </div>
  );
}

export default Alerts;
