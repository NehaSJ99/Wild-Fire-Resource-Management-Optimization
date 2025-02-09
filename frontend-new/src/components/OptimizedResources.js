import React, { useState, useEffect } from "react";
import axios from "axios";

const OptimizedResources = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.post("/optimize_resources");
                
                setData(response.data.resources_allocted);
                setLoading(false);
            } catch (error) {
                console.error("Error fetching data:", error);
                setError("Failed to fetch optimized resources");
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) return <p>Loading...</p>;
    if (error) return <p>{error}</p>;

    return (
        <div>
            <h1>Optimized Resources</h1>
            {data ? (
                <ul>
                    <li>Firefighters: {data.firefighters}</li>
                    <li>Trucks: {data.trucks}</li>
                    <li>Helicopters: {data.helicopters}</li>
                </ul>
            ) : (
                <p>No data available</p>
            )}
        </div>
    );
};

export default OptimizedResources;
