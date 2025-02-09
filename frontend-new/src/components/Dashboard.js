import React from "react";
import { Container, Typography, Card, CardContent, Button, Grid, CardActionArea, Box } from "@mui/material";
import { styled } from "@mui/material/styles";
import axios from "axios";
import { useNavigate } from "react-router-dom"; // add react-router hook

// Styled Components for Cards
const StyledCard = styled(Card)(({ theme }) => ({
  height: "100%", // Ensures all cards have the same height
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between", // Pushes the button to the bottom
  boxShadow: "0px 10px 30px rgba(0, 0, 0, 0.15)",
  borderRadius: "12px",
  transition: "all 0.3s ease-in-out",
  "&:hover": {
    transform: "scale(1.05)",
    boxShadow: "0px 15px 40px rgba(0, 0, 0, 0.2)",
  },
  background: "linear-gradient(135deg, #FF7A00, #FF3A00)", // Gradient background
}));

const StyledCardContent = styled(CardContent)(({ theme }) => ({
  flexGrow: 1,
  textAlign: "center",
  padding: theme.spacing(3),
  color: "#fff",
}));

const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "#000", // Set button background to black
  color: "#fff", // White text for contrast
  padding: "12px 20px",
  borderRadius: "8px",
  "&:hover": {
    backgroundColor: "#333", // Slightly lighter black on hover
    transform: "scale(1.05)",
  },
  transition: "transform 0.3s ease-in-out",
  margin: theme.spacing(2), // Adds spacing inside the card
}));

const Dashboard = () => {
  // API Handlers

  const navigate = useNavigate();

  const handlePredictSpread = () => {
    // Instead of calling axios directly, just navigate to the /predict_results page.
    navigate("/predict_results");
  };


  
  const handleOptimizeResources = async () => {
    try {
      const response = await axios.post("http://localhost:5000/optimize_resources"); 
      console.log("Full response data:", response.data);
  
      if (response.data.status === "success") {
        alert("Resource optimization complete! Check console for details.");
        console.log("Optimization Results:", response.data.data); // Data should be 'results' from resource_optimized.py
      } else {
        alert("Failed to optimize resources.");
      }
    } catch (error) {
      console.error("Error optimizing resources:", error);
      alert("Failed to optimize resources.");
    }
  };
  

 
  const handleGenerateMap = async () => {
    try {
      // Trigger the map generation
      const response = await fetch("http://localhost:5000/generate_map");
  
      if (response.ok) {
        // After the map is generated, open the evacuation map in a new tab
        const mapUrl = "http://localhost:5000/evacuation_map";
        window.open(mapUrl, "_blank");
      } else {
        alert("Error generating the map.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Error generating the map.");
    }
  };

  return (
    <Container>
      <Typography variant="h4" align="center" sx={{ fontWeight: "bold", color: "#333", marginBottom: "50px", marginTop: "30px"}}>
        Wildfire Resource Management Dashboard
      </Typography>
      <Grid container spacing={4} justifyContent="center">
        {/* Card 1: Predict the Spread */}
        <Grid item xs={12} sm={6} md={4}>
          <StyledCard>
            <CardActionArea>
              <StyledCardContent>
                <Typography variant="h5" sx={{ fontSize: "24px", fontWeight: "500", color: "#fff" }}>
                  Predict the Spread
                </Typography>
                <Typography variant="body2" sx={{ fontSize: "16px", color: "#fff" }}>
                  Analyze fire spread patterns using prediction models and data.
                </Typography>
              </StyledCardContent>
            </CardActionArea>
            <Box display="flex" justifyContent="center">
              <StyledButton variant="contained" onClick={handlePredictSpread}>
                Predict
              </StyledButton>
            </Box>
          </StyledCard>
        </Grid>

        {/* Card 2: Optimize the Resources */}
        <Grid item xs={12} sm={6} md={4}>
          <StyledCard>
            <CardActionArea>
              <StyledCardContent>
                <Typography variant="h5" sx={{ fontSize: "24px", fontWeight: "500", color: "#fff" }}>
                  Optimize the Resources
                </Typography>
                <Typography variant="body2" sx={{ fontSize: "16px", color: "#fff" }}>
                  Deploy resources efficiently to fight the wildfire and minimize loss.
                </Typography>
              </StyledCardContent>
            </CardActionArea>
            <Box display="flex" justifyContent="center">
              <StyledButton variant="contained" onClick={handleOptimizeResources}>
                Optimize
              </StyledButton>
            </Box>
          </StyledCard>
        </Grid>

        {/* Card 3: Emergency Evacuation Plan */}
        <Grid item xs={12} sm={6} md={4}>
          <StyledCard>
            <CardActionArea>
              <StyledCardContent>
                <Typography variant="h5" sx={{ fontSize: "24px", fontWeight: "500", color: "#fff" }}>
                  Emergency Evacuation Plan
                </Typography>
                <Typography variant="body2" sx={{ fontSize: "16px", color: "#fff" }}>
                  Plan evacuation routes and actions to protect civilians and resources.
                </Typography>
              </StyledCardContent>
            </CardActionArea>
            <Box display="flex" justifyContent="center">
              <StyledButton variant="contained" onClick={handleGenerateMap}>
                Plan Evacuation
              </StyledButton>
            </Box>
          </StyledCard>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
