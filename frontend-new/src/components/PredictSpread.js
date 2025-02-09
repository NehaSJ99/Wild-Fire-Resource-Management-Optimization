import React from "react";

const PredictSpread = () => {
  // Image should be placed inside the "public" folder (e.g., `public/image.png`)
  const imageSrc = process.env.PUBLIC_URL + "/image.png";

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Predicted Spread Results</h2>
      <img
        src={imageSrc}
        alt="Wildfire Spread Prediction"
        style={{ maxWidth: "95%", border: "5px solid #333", borderRadius: "0px" }}
      />
    </div>
  );
};

export default PredictSpread;