const BASE_URL = "http://localhost:8000";

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const districtSelect = document.getElementById('district_select');
    const districtTotal2020 = document.getElementById('district_total_2020');
    const districtFatal2020 = document.getElementById('district_fatal_2020');
    const districtLat = document.getElementById('district_lat');
    const districtLon = document.getElementById('district_lon');
    const previewDiv = document.getElementById('district-preview');
    const previewText = document.getElementById('preview-text');
    const predictBtn = document.getElementById('predict-btn');
    const form = document.getElementById('prediction-form');

    let districtData = [];

    // Initialize Dashboard
    async function initDashboard() {
        try {
            await Promise.all([
                fetchSummary(),
                fetchVehicleStats(),
                fetchComparison(),
                fetchDistricts()
            ]);
        } catch (error) {
            console.error("Dashboard initialization failed:", error);
        }
    }

    async function fetchSummary() {
        const response = await fetch(`${BASE_URL}/dashboard/summary`);
        if (!response.ok) return;
        const data = await response.json();
        
        document.getElementById('metric-accidents-2020').textContent = data.total_accidents_2020.toLocaleString();
        document.getElementById('metric-accidents-2021').textContent = data.total_accidents_2021.toLocaleString();
        document.getElementById('metric-fatal-2020').textContent = data.total_deaths_2020.toLocaleString();
        document.getElementById('metric-fatal-2021').textContent = data.total_deaths_2021.toLocaleString();
    }

    async function fetchVehicleStats() {
        const response = await fetch(`${BASE_URL}/dashboard/vehicle-stats`);
        if (!response.ok) return;
        const data = await response.json();

        const ctx = document.getElementById('vehicleChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Lorries', 'Buses', 'Cars/Jeeps', '3-Wheelers', '2-Wheelers', 'Others'],
                datasets: [{
                    data: [
                        data.lorries, data.buses, data.cars_jeeps, 
                        data.three_wheelers, data.two_wheelers, data.others
                    ],
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#f8fafc' } }
                }
            }
        });
    }

    async function fetchComparison() {
        const response = await fetch(`${BASE_URL}/dashboard/comparison`);
        if (!response.ok) return;
        const { comparison } = await response.json();

        const ctx = document.getElementById('comparisonChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: comparison.map(c => c.district),
                datasets: [
                    {
                        label: '2020 Accidents',
                        data: comparison.map(c => c.accidents_2020),
                        backgroundColor: '#3b82f6'
                    },
                    {
                        label: '2021 Accidents',
                        data: comparison.map(c => c.accidents_2021),
                        backgroundColor: '#ef4444'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                },
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                }
            }
        });
    }

    async function fetchDistricts() {
        const response = await fetch(`${BASE_URL}/districts`);
        if (!response.ok) return;
        const { districts } = await response.json();
        
        districtData = districts;
        
        districtSelect.innerHTML = '<option value="" disabled selected>Select a District...</option>';
        districts.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.district;
            opt.textContent = d.district;
            districtSelect.appendChild(opt);
        });
    }

    // Handle District Selection
    districtSelect.addEventListener('change', async (e) => {
        const selected = districtData.find(d => d.district === e.target.value);
        if (selected) {
            districtTotal2020.value = selected.total_2020;
            districtFatal2020.value = selected.fatal_2020;
            districtLat.value = selected.latitude;
            districtLon.value = selected.longitude;
            
            previewText.innerHTML = `${selected.total_2020} accidents in 2020, with ${selected.fatal_2020} fatalities.<br><small style="color: #64748b;">Fetching live environmental data...</small>`;
            previewDiv.classList.remove('hidden');
            predictBtn.disabled = false;
            
            // Fetch live environmental data using Open-Meteo API
            try {
                const tempInput = document.getElementById('temperature');
                const rainInput = document.getElementById('rainfall');
                const visInput = document.getElementById('visibility');
                
                // Clear existing values to show it's updating
                tempInput.value = '';
                rainInput.value = '';
                visInput.value = '';
                
                const response = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${selected.latitude}&longitude=${selected.longitude}&current=temperature_2m,rain,visibility`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.current) {
                        tempInput.value = data.current.temperature_2m;
                        rainInput.value = data.current.rain;
                        // Visibility is in meters, convert to km
                        if (data.current.visibility !== undefined) {
                            visInput.value = (data.current.visibility / 1000).toFixed(1);
                        } else {
                            visInput.value = 10.0; // fallback
                        }
                        previewText.innerHTML = `${selected.total_2020} accidents in 2020, with ${selected.fatal_2020} fatalities.<br><small style="color: #10b981;">Live environmental data loaded.</small>`;
                    }
                } else {
                    throw new Error("API response not ok");
                }
            } catch (err) {
                console.error("Failed to fetch live weather data:", err);
                previewText.innerHTML = `${selected.total_2020} accidents in 2020, with ${selected.fatal_2020} fatalities.<br><small style="color: #ef4444;">Failed to load live weather, using defaults.</small>`;
                document.getElementById('temperature').value = 28.0;
                document.getElementById('rainfall').value = 0.0;
                document.getElementById('visibility').value = 10.0;
            }
        }
    });

    // Handle Prediction Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        predictBtn.textContent = "Analyzing...";
        predictBtn.disabled = true;
        
        const payload = {
            total_2020: parseFloat(districtTotal2020.value),
            fatal_2020: parseFloat(districtFatal2020.value),
            latitude: parseFloat(districtLat.value),
            longitude: parseFloat(districtLon.value),
            temperature: parseFloat(document.getElementById('temperature').value),
            rainfall: parseFloat(document.getElementById('rainfall').value),
            visibility: parseFloat(document.getElementById('visibility').value)
        };
        
        try {
            const response = await fetch(`${BASE_URL}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) throw new Error("API Error");
            
            const result = await response.json();
            displayResults(result);
        } catch (error) {
            alert("Prediction failed. Ensure the backend is running.");
        } finally {
            predictBtn.textContent = "Analyze Today's Route Risk";
            predictBtn.disabled = false;
        }
    });

    function displayResults(data) {
        const section = document.getElementById('results-section');
        section.classList.remove('hidden');
        setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        
        const badge = document.getElementById('risk-badge');
        const levelText = document.getElementById('risk-level');
        const weatherContextDisplay = document.getElementById('weather-context-display');
        
        badge.className = 'risk-badge'; // reset
        if (data.risk_level === "Low") badge.classList.add('risk-low');
        else if (data.risk_level === "Medium") badge.classList.add('risk-med');
        else if (data.risk_level === "High") badge.classList.add('risk-high');
        
        levelText.textContent = `${data.risk_level} Travel Risk for Today`;
        
        if (data.weather_context) {
            weatherContextDisplay.innerHTML = `
                <strong>Temp:</strong> ${data.weather_context.temperature}°C &nbsp;|&nbsp; 
                <strong>Rain:</strong> ${data.weather_context.rainfall}mm &nbsp;|&nbsp; 
                <strong>Vis:</strong> ${data.weather_context.visibility}km<br>
                <strong>Time:</strong> ${data.weather_context.hour_of_day}:00 &nbsp;|&nbsp; 
                <strong>Traffic:</strong> ~${data.weather_context.traffic_volume} vehicles/hr
            `;
        }
        
        updateBar('low', data.probabilities["Low"]);
        updateBar('med', data.probabilities["Medium"]);
        updateBar('high', data.probabilities["High"]);
    }
    
    function updateBar(type, prob) {
        const percent = Math.round(prob * 100);
        document.getElementById(`prob-${type}-val`).textContent = `${percent}%`;
        setTimeout(() => {
            document.getElementById(`prob-${type}`).style.width = `${percent}%`;
        }, 50);
    }

    // Run Initialization
    initDashboard();
});
