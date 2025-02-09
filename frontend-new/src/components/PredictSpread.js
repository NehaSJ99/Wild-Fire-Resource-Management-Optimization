import React from "react";

const PredictSpread = () => {
  const imageSrc = process.env.PUBLIC_URL + "/image.png";

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Predicted Spread Results</h2>
      <img
        src={imageSrc}
        alt="Wildfire Spread Prediction"
        style={{ maxWidth: "200%", border: "0px solid #333", borderRadius: "0px" }}
      />
    </div>
  );
};

export default PredictSpread;
