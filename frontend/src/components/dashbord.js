import React, { useState } from "react";
import axios from "axios";

function Dashboard() {
  const [data, setData] = useState({ temp: "", humidity: "", wind_speed: "" });
  const [risk, setRisk] = useState(null);

  const handleChange = (e) => setData({ ...data, [e.target.name]: e.target.value });

  const handlePredict = async () => {
    const res = await axios.post("http://localhost:5000/predict", data);
    setRisk(res.data.fire_risk ? "🔥 High Risk" : "✅ Low Risk");
  };

  return (
    <div>
      <h2>Fire Risk Prediction</h2>
      <input name="temp" placeholder="Temperature" onChange={handleChange} />
      <input name="humidity" placeholder="Humidity" onChange={handleChange} />
      <input name="wind_speed" placeholder="Wind Speed" onChange={handleChange} />
      <button onClick={handlePredict}>Predict</button>
      {risk && <p>Risk Level: {risk}</p>}
    </div>
  );
}

export default Dashboard;
