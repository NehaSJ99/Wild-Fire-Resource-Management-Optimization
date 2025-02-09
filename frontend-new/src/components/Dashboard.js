import React from "react";
import { Container, Typography, Card, CardContent } from "@mui/material";

const Dashboard = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6">🔥 Fire Prediction & Resource Allocation</Typography>
          <Typography variant="body1">
            View fire risk predictions, optimize resource deployment, and monitor emergency response status.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Dashboard;
