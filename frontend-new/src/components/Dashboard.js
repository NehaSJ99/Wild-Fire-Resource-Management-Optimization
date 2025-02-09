import React from "react";
import { Container, Typography, Card, CardContent, Button, Grid, CardActionArea } from "@mui/material";
import { styled } from "@mui/material/styles";
import axios from "axios";

// Styled Components for Cards
const StyledCard = styled(Card)(({ theme }) => ({
  height: "100%",
  display: "flex",
  flexDirection: "column",
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
  color: "#fff", // White text for contrast
}));

const StyledButton = styled(Button)(({ theme }) => ({
  marginTop: "auto",
  backgroundColor: theme.palette.primary.main,
  color: "#fff",
  padding: "12px 20px",
  borderRadius: "8px",
  "&:hover": {
    backgroundColor: theme.palette.primary.dark,
    transform: "scale(1.05)",
  },
  transition: "transform 0.3s ease-in-out",
}));

const Dashboard = () => {
  // Handle API request for Predicting the Spread
  const handlePredictSpread = async () => {
    try {
      const response = await axios.post("http://localhost:5000/predict-spread");
      alert(response.data.message);  // Handle the response
    } catch (error) {
      console.error("Error predicting spread:", error);
      alert("Failed to predict the spread.");
    }
  };

  // Handle API request for Optimizing Resources
  const handleOptimizeResources = async () => {
    try {
      const response = await axios.post("http://localhost:5000/optimize-resources");
      alert(response.data.message);  // Handle the response
    } catch (error) {
      console.error("Error optimizing resources:", error);
      alert("Failed to optimize resources.");
    }
  };

  // Handle API request for Emergency Evacuation Plan
  const handleEvacuationPlan = async () => {
    try {
      const response = await axios.post("http://localhost:5000/emergency-evacuation");
      alert(response.data.message);  // Handle the response
    } catch (error) {
      console.error("Error planning evacuation:", error);
      alert("Failed to plan evacuation.");
    }
  };

  return (
    <Container>
      <Typography variant="h4" gutterBottom align="center" sx={{ fontWeight: "bold", color: "#333" }}>
        Wildfire Resource Management Dashboard
      </Typography>
      <Grid container spacing={3} justifyContent="center" alignItems="center" sx={{ marginTop: "40px" }}>
        {/* Card 1: Predict the Spread */}
        <Grid item xs={12} sm={4}>
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
            <StyledButton variant="contained" onClick={handlePredictSpread}>
              Predict
            </StyledButton>
          </StyledCard>
        </Grid>

        {/* Card 2: Optimize the Resources */}
        <Grid item xs={12} sm={4}>
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
            <StyledButton variant="contained" onClick={handleOptimizeResources}>
              Optimize
            </StyledButton>
          </StyledCard>
        </Grid>

        {/* Card 3: Emergency Evacuation Plan */}
        <Grid item xs={12} sm={4}>
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
            <StyledButton variant="contained" onClick={handleEvacuationPlan}>
              Plan Evacuation
            </StyledButton>
          </StyledCard>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
