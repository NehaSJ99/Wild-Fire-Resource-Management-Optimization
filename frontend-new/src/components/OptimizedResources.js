import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Typography, CircularProgress, Box, Card, CardContent, Grid, Alert } from "@mui/material";

const OptimizedResources = () => {
  const [data, setData] = useState(null); // Store the optimization results
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null); // Error state

  useEffect(() => {
    // Fetch data when the component is mounted
    const fetchData = async () => {
      try {
        // Make the POST request to Flask API
        const response = await axios.post("http://localhost:5000/optimize_resources");

        // Check if the response is successful
        if (response.data.status === "success") {
          setData(response.data.data); // Set data state if successful
        } else {
          setError("Optimization failed: " + response.data.message); // Set error if the optimization failed
        }
        setLoading(false); // End loading after data is fetched
      } catch (error) {
        console.error("Error fetching data:", error);
        setError("Failed to fetch optimized resources");
        setLoading(false);
      }
    };

    fetchData(); // Call the fetch function
  }, []); // Empty dependency array ensures this effect runs only once when the component is mounted

  // Render loading spinner while fetching
  if (loading) return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
      <CircularProgress />
    </Box>
  );

  // Render error message if there is an error
  if (error) return (
    <Box sx={{ width: '100%', marginTop: 4 }}>
      <Alert severity="error">{error}</Alert>
    </Box>
  );

  // Render the optimization results
  return (
    <Container maxWidth="lg" sx={{ marginTop: 4 }}>
      <Typography
        variant="h4"
        sx={{
          fontWeight: "bold",
          marginBottom: 3,
          background: "linear-gradient(135deg, #FF7A00, #FF3A00)",
          WebkitBackgroundClip: "text", // Makes the gradient fill the text
          color: "transparent", // Makes text color transparent so gradient is visible
        }}
      >
        Optimized Resources
      </Typography>

      {data && data.length > 0 ? (
        <Grid container spacing={3}>
          {data.map((item, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card elevation={3} sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                    From: {item.from} to: {item.to}
                  </Typography>
                  <Typography variant="body1" sx={{ marginBottom: 1 }}>
                    <strong>Firefighters:</strong> {item.firefighters}
                  </Typography>
                  <Typography variant="body1" sx={{ marginBottom: 1 }}>
                    <strong>Water:</strong> {item.water} litres (Transporting from water tanker)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Move firefighters where required
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Typography variant="body1" color="text.secondary" sx={{ marginTop: 2 }}>
          No data available
        </Typography>
      )}
    </Container>
  );
};

export default OptimizedResources;
