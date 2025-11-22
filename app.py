# solar_app.py
import math
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Solar Energy Analyzer",
    layout="wide"
)

st.title("🔆 Solar Energy Analyzer")
st.write(
    "Estimate annual solar energy yield for different locations and system configurations. "
    "This is a simplified engineering model – you can refine the data and equations later."
)

# ---------------------------
# 1. SIMPLE LOCATION DATABASE
# ---------------------------
# You can replace these with real data later (kWh/m²/day global horizontal irradiation)
SOLAR_LOCATIONS = {
    "Kolkata, India": {
        "lat": 22.6,
        "ghi_daily": 5.0  # approx
    },
    "Hamburg, Germany": {
        "lat": 53.5,
        "ghi_daily": 2.9
    },
    "Munich, Germany": {
        "lat": 48.1,
        "ghi_daily": 3.3
    },
    "Delhi, India": {
        "lat": 28.6,
        "ghi_daily": 5.3
    },
}

# For monthly distribution, we just use a normalized shape (rough sinusoidal-like)
# Jan..Dec factors that sum to 1.0 (you can tune these)
MONTHLY_SHAPE = [0.07, 0.075, 0.085, 0.09, 0.095, 0.095,
                 0.095, 0.09, 0.085, 0.08, 0.075, 0.07]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------------------
# 2. SIDEBAR INPUTS
# ---------------------------
st.sidebar.header("Inputs")

location = st.sidebar.selectbox(
    "Location",
    options=list(SOLAR_LOCATIONS.keys()),
    index=0
)

system_size_kw = st.sidebar.number_input(
    "System size (kW)",
    min_value=0.5,
    max_value=100.0,
    value=5.0,
    step=0.5
)

panel_efficiency = st.sidebar.slider(
    "Panel efficiency (%)",
    min_value=15.0,
    max_value=25.0,
    value=19.0,
    step=0.5
)

tilt_angle = st.sidebar.slider(
    "Tilt angle (degrees)",
    min_value=0,
    max_value=60,
    value=int(SOLAR_LOCATIONS[location]["lat"]),  # approximate: latitude
    step=1
)

orientation = st.sidebar.selectbox(
    "Orientation",
    options=["South (ideal in N hemisphere)",
             "South-East / South-West",
             "East / West",
             "Flat / Horizontal"]
)

system_losses_pct = st.sidebar.slider(
    "Total system losses (soiling, wiring, inverter, etc.) [%]",
    min_value=5,
    max_value=30,
    value=15,
    step=1
)

# ---------------------------
# 3. SIMPLE CALCULATIONS
# ---------------------------
loc_data = SOLAR_LOCATIONS[location]
ghi_daily = loc_data["ghi_daily"]  # kWh/m²/day (horizontal)

# Orientation / tilt factor – super simplified fudge factors
if orientation == "South (ideal in N hemisphere)":
    orientation_factor = 1.0
elif orientation == "South-East / South-West":
    orientation_factor = 0.95
elif orientation == "East / West":
    orientation_factor = 0.90
else:  # Flat / Horizontal
    orientation_factor = 0.88

# Very rough tilt factor: slight boost around latitude, penalize extremes
lat = loc_data["lat"]
tilt_diff = abs(tilt_angle - lat)
# Simple piecewise penalty: 0–20° diff => small penalty, >20 => more
if tilt_diff <= 10:
    tilt_factor = 1.0
elif tilt_diff <= 20:
    tilt_factor = 0.96
else:
    tilt_factor = 0.90

# Daily irradiation on tilted plane
daily_irradiation_tilt = ghi_daily * orientation_factor * tilt_factor  # kWh/m²/day

# Performance ratio from system losses (very simplified)
pr = 1.0 - system_losses_pct / 100.0

# Specific yield (kWh per kWp per year)
# classic approx: specific_yield = daily_irradiation_tilt * 365 * PR / reference_irr
# Here we assume 1 kWp ~ 1 kW/m² for simplicity.
specific_yield = daily_irradiation_tilt * 365.0 * pr  # kWh/kWp/year (approx)

# Total annual energy
annual_energy_kwh = specific_yield * system_size_kw  # kWh/year

# Capacity factor
capacity_factor = annual_energy_kwh / (system_size_kw * 8760.0)  # fraction

# Monthly energy split
monthly_energies = [annual_energy_kwh * f for f in MONTHLY_SHAPE]
df_monthly = pd.DataFrame({
    "Month": MONTH_NAMES,
    "Energy (kWh)": monthly_energies
}).set_index("Month")

# ---------------------------
# 4. OUTPUTS
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Key Results")

    st.metric(
        "Daily solar irradiation on tilted plane",
        f"{daily_irradiation_tilt:.2f} kWh/m²/day"
    )
    st.metric(
        "Specific yield",
        f"{specific_yield:.0f} kWh/kWp/year"
    )
    st.metric(
        "Annual energy output",
        f"{annual_energy_kwh:.0f} kWh/year"
    )
    st.metric(
        "Capacity factor",
        f"{capacity_factor*100:.1f} %"
    )

with col2:
    st.subheader("Monthly Energy Production")
    st.bar_chart(df_monthly)

st.markdown("---")
st.subheader("Assumptions & Notes")

st.write(
    """
- Location data (irradiation) is **dummy/approximate** – replace with real datasets later.
- Orientation and tilt effects are modeled with simple multipliers, not full geometry or time-of-day effects.
- Performance Ratio (PR) is derived directly from the total losses slider (PR = 1 − losses).
- Capacity factor is computed as:  
  \\( CF = \\frac{E_{annual}}{P_{rated} \\times 8760} \\).
- This version is meant as a **basic framework** – you can plug in:
  - Real monthly irradiance data per location,
  - Temperature effects,
  - Financial analysis (LCOE, payback),
  - CO₂ savings.
"""
)
