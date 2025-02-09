import React, { useState, useEffect } from "react";
import axios from "axios";

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

    // Render loading message while fetching
    if (loading) return <p>Loading...</p>;

    // Render error message if there is an error
    if (error) return <p>{error}</p>;

    // Render the optimization results
    return (
        <div>
            <h1>Optimized Resources</h1>
            {data ? (
                <ul>
                    {data.map((item, index) => (
                        <li key={index}>
                            <p><strong>From:</strong> {item.from} <strong>to:</strong> {item.to}</p>
                            <p><strong>Firefighters:</strong> {item.firefighters}</p>
                            <p><strong>Water:</strong> {item.water}</p>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No data available</p>
            )}
        </div>
    );
};

export default OptimizedResources;
