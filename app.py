# solar_app.py
import math
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Solar Energy Analyzer",
    layout="wide"
)

st.title("🔆 Solar Energy Analyzer ( Data-Driven Version)")
st.write(
    "Estimate annual solar energy yield for different locations and system configurations. "
    "Uses approximate but realistic solar irradiation data per location."
)

# ----------------------------------------------------
# 1. LOCATION DATABASE – MONTHLY GHI (kWh/m² per month)
#    Values are approximate typical data, not exact.
# ----------------------------------------------------
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# kWh/m²/month – rough but realistic patterns
SOLAR_LOCATIONS = {
    "Kolkata, India": {
        "lat": 22.6,
        "monthly_ghi": [120, 115, 140, 160, 170, 155, 150, 150, 145, 130, 110, 105],
    },
    "Delhi, India": {
        "lat": 28.6,
        "monthly_ghi": [130, 135, 160, 180, 200, 190, 185, 180, 160, 140, 120, 115],
    },
    "Hamburg, Germany": {
        "lat": 53.5,
        "monthly_ghi": [25, 45, 80, 115, 150, 165, 160, 135, 95, 60, 30, 18],
    },
    "Munich, Germany": {
        "lat": 48.1,
        "monthly_ghi": [40, 60, 100, 135, 165, 175, 175, 150, 110, 70, 40, 30],
    },
    "Berlin, Germany": {
        "lat": 52.5,
        "monthly_ghi": [30, 50, 90, 125, 155, 170, 165, 140, 100, 65, 35, 22],
    },
}

def get_annual_and_daily_ghi(location_data: dict):
    monthly = location_data["monthly_ghi"]
    annual_ghi = sum(monthly)  # kWh/m²/year
    daily_ghi = annual_ghi / 365.0  # kWh/m²/day
    return annual_ghi, daily_ghi

# ----------------------------------------------------
# 2. SIDEBAR INPUTS
# ----------------------------------------------------
st.sidebar.header("Inputs")

location = st.sidebar.selectbox(
    "Location",
    options=list(SOLAR_LOCATIONS.keys()),
    index=0
)
loc_data = SOLAR_LOCATIONS[location]
annual_ghi, ghi_daily = get_annual_and_daily_ghi(loc_data)

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
    value=int(loc_data["lat"]),
    step=1,
    key=f"tilt_angle_{location}"
)

orientation = st.sidebar.selectbox(
    "Orientation",
    options=[
        "South (ideal in N hemisphere)",
        "South-East / South-West",
        "East / West",
        "Flat / Horizontal"
    ]
)

system_losses_pct = st.sidebar.slider(
    "Total system losses (soiling, wiring, inverter, etc.) [%]",
    min_value=5,
    max_value=30,
    value=15,
    step=1
)

# ----------------------------------------------------
# 3. CALCULATIONS
# ----------------------------------------------------
# Orientation factor – simple multipliers
if orientation == "South (ideal in N hemisphere)":
    orientation_factor = 1.0
elif orientation == "South-East / South-West":
    orientation_factor = 0.95
elif orientation == "East / West":
    orientation_factor = 0.90
else:  # Flat / Horizontal
    orientation_factor = 0.88

lat = loc_data["lat"]
tilt_diff = abs(tilt_angle - lat)
if tilt_diff <= 10:
    tilt_factor = 1.0
elif tilt_diff <= 20:
    tilt_factor = 0.96
else:
    tilt_factor = 0.90

# Adjust daily GHI by orientation & tilt
daily_irradiation_tilt = ghi_daily * orientation_factor * tilt_factor  # kWh/m²/day

# System losses → Performance Ratio
pr = 1.0 - system_losses_pct / 100.0

# Specific yield & annual energy
# Assuming 1 kWp ~ 1 kW/m² effective; this is a simplification.
specific_yield = daily_irradiation_tilt * 365.0 * pr  # kWh/kWp/year (approx)
annual_energy_kwh = specific_yield * system_size_kw

capacity_factor = annual_energy_kwh / (system_size_kw * 8760.0)

# Monthly energy distribution based on monthly_ghi share
monthly_ghi = loc_data["monthly_ghi"]
annual_ghi_tilt = annual_ghi * orientation_factor * tilt_factor
if annual_ghi_tilt > 0:
    monthly_fractions = [m / annual_ghi for m in monthly_ghi]
else:
    monthly_fractions = [1.0 / 12.0] * 12

monthly_energies = [annual_energy_kwh * f for f in monthly_fractions]

df_monthly = pd.DataFrame({
    "Month": MONTH_NAMES,
    "Energy (kWh)": monthly_energies
}).set_index("Month")

# ----------------------------------------------------
# 4. OUTPUTS
# ----------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Key Results")

    st.metric(
        "Daily solar irradiation (horizontal)",
        f"{ghi_daily:.2f} kWh/m²/day"
    )
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
- Monthly solar irradiation values are approximate, location-specific typical values (kWh/m²/month).
- Annual GHI is the sum of monthly values; daily GHI = annual GHI / 365.
- Tilt and orientation are modeled with simple multipliers, not full sun-path geometry.
- Performance Ratio (PR) is derived directly from the total losses slider: PR = 1 − losses.
- Capacity factor = annual energy / (rated power × 8760).
"""
)
