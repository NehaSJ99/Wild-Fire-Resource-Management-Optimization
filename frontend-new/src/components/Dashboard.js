import React, { useState } from "react";
import { Container, Typography, Card, CardContent, Button, Grid, CardActionArea, Box, CircularProgress } from "@mui/material";
import { styled } from "@mui/material/styles";
import axios from "axios";
import { useNavigate } from "react-router-dom"; 
import { Snackbar } from "@mui/material";


// Styled Components
const StyledCard = styled(Card)(({ theme }) => ({
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between",
  boxShadow: "0px 10px 30px rgba(0, 0, 0, 0.15)",
  borderRadius: "12px",
  transition: "all 0.3s ease-in-out",
  "&:hover": {
    transform: "scale(1.05)",
    boxShadow: "0px 15px 40px rgba(0, 0, 0, 0.2)",
  },
  background: "linear-gradient(135deg, #FF7A00, #FF3A00)",
}));

const StyledCardContent = styled(CardContent)(({ theme }) => ({
  flexGrow: 1,
  textAlign: "center",
  padding: theme.spacing(3),
  color: "#fff",
}));

const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "#000",
  color: "#fff",
  padding: "12px 20px",
  borderRadius: "8px",
  "&:hover": {
    backgroundColor: "#333",
    transform: "scale(1.05)",
  },
  transition: "transform 0.3s ease-in-out",
  margin: theme.spacing(2),
}));

const Dashboard = () => {
  const navigate = useNavigate();
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);


  const handleUpload = () => {
    setLoadingUpload(true);
    // Add your file upload logic here
    setTimeout(() => {
      setLoadingUpload(false);
      alert("File uploaded successfully!");
    }, 2000); // Simulate upload delay
  };

  const handlePredictSpread = () => {
    setLoadingPredict(true);
    setTimeout(() => {
      setLoadingPredict(false);
      navigate("/predict_results");
    }, 20000); // 20 seconds delay
  };

  const handleOptimizeResources = async () => {
    try {
      const response = await axios.post("http://localhost:5000/optimize_resources");
      console.log("Full response data:", response.data);
  
      if (response.data.status === "success") {
        alert("Resource optimization complete! Check console for details.");
        console.log("Optimization Results:", response.data.data);
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
      const response = await fetch("http://localhost:5000/generate_map");
      if (response.ok) {
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
  
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleFileUpload = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:5000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.status === "success") {
        setUploadSuccess(true);
      } else {
        alert("File upload failed.");
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Error uploading file.");
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

            {/* File upload */}
            <Box display="flex" justifyContent="center" sx={{ padding: "10px" }}>
              <input type="file" onChange={handleFileChange} />
            </Box>

          
            <Snackbar
              open={uploadSuccess}
              autoHideDuration={6000}
              onClose={() => setUploadSuccess(false)}
              message="File uploaded successfully"
            />
            {/* Predict button */}
            <Box display="flex" justifyContent="center">
              <StyledButton variant="contained" onClick={handlePredictSpread} disabled={loadingPredict}>
                {loadingPredict ? <CircularProgress size={24} sx={{ color: "#fff" }} /> : "Predict"}
              </StyledButton>
            </Box>

            {/* Success message */}
            <Snackbar
              open={uploadSuccess}
              autoHideDuration={6000}
              onClose={() => setUploadSuccess(false)}
              message="File uploaded successfully"
            />
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
