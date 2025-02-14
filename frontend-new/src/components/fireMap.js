import React, { useState } from "react";
import { MapContainer, TileLayer, Popup, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import axios from "axios";
import { Button, TextField, Container,CircularProgress,Typography } from "@mui/material";
import { styled } from "@mui/material/styles";

const StyledButton = styled(Button)(({ theme }) => ({
    backgroundColor: "#000",
    color: "#fff",
    padding: "12px 20px",
    borderRadius: "8px",
    fontSize: "16px",
    fontWeight: "bold",
    "&:hover": {
        backgroundColor: "#333",
        transform: "scale(1.05)",
    },
    transition: "transform 0.3s ease-in-out",
    marginLeft: theme.spacing(2),
}));

const FireMap = () => {
    const [country, setCountry] = useState("IND");
    const [days, setDays] = useState(3);
    const [fireData, setFireData] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchFireData = async () => {
        setLoading(true);
        try {
            const response = await axios.get("http://localhost:5000/detect-fire", {
                params: { country, days },
            });

            setFireData(response.data.data);
        } catch (error) {
            console.error("Error fetching fire data:", error);
            setFireData([]);
        }
        setLoading(false);
    };

    return (
        <Container maxWidth="md" style={{ textAlign: "center", marginTop: "20px" }}>
            <Typography variant="h4" gutterBottom>
                🔥 Wildfire Map
            </Typography>

            <div style={{ display: "flex", justifyContent: "center", gap: "10px", marginBottom: "15px" }}>
                <TextField
                    label="Country Code"
                    variant="outlined"
                    value={country}
                    onChange={(e) => setCountry(e.target.value.toUpperCase())}
                    style={{ width: "150px" }}
                />

                <TextField
                    label="Days"
                    type="number"
                    variant="outlined"
                    value={days}
                    inputProps={{ min: 1, max: 10 }}
                    onChange={(e) => setDays(Number(e.target.value))}
                    style={{ width: "100px" }}
                />

                <StyledButton onClick={fetchFireData} disabled={loading}>
                    {loading ? <CircularProgress size={24} sx={{ color: "#fff" }} /> : "Detect Fires"}
                </StyledButton>
            </div>
          
            <div style={{ borderRadius: "12px", overflow: "hidden", boxShadow: "0px 4px 12px rgba(0,0,0,0.2)" }}>
                <MapContainer center={[20, 77]} zoom={4} style={{ height: "500px", width: "100%" }}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

                    {fireData.map((fire, index) => (
                        <CircleMarker
                            key={index}
                            center={[fire.latitude, fire.longitude]}
                            radius={5}
                            fillColor={fire.confidence > 75 ? "red" : "yellow"}
                            fillOpacity={0.8}
                            stroke={false}
                        >
                            <Popup>
                                <strong>Brightness:</strong> {fire.brightness} <br />
                                <strong>Confidence:</strong> {fire.confidence}%
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>
            </div>
        </Container>
    );
};

export default FireMap;
