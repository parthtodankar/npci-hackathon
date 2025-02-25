import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import time, timedelta

# Load dataset from CSV with proper datetime handling
@st.cache_data
def load_traffic_data():
    df = pd.read_csv('/Users/todankar/Desktop/traffic management/Bangalore_1Day_NETC.csv')
    
    # Fix datetime parsing
    def parse_datetime(x):
        try:
            return pd.to_datetime(x, format='%d-%m-%Y %H:%M')
        except:
            time_part = x.split()[-1]
            return pd.to_datetime(f'01-01-2024 {time_part}', format='%d-%m-%Y %H:%M')
    
    df['initiated_time'] = df['initiated_time'].apply(parse_datetime)
    
    # Clean and preprocess data
    df[['latitude', 'longitude']] = df['geocode'].str.split(',', expand=True).astype(float)
    df['hour'] = df['initiated_time'].dt.hour
    df['minute'] = df['initiated_time'].dt.minute
    return df

def calculate_lane_allocation(north, south, total_lanes=8):
    total = north + south
    if total == 0:
        return total_lanes//2, total_lanes//2
    
    north_ratio = north / total
    south_ratio = south / total
    
    north_lanes = max(1, round(north_ratio * total_lanes))
    south_lanes = max(1, total_lanes - north_lanes)
    
    return north_lanes, south_lanes

def main():
    st.set_page_config(page_title="Bangalore Toll Lane Manager", layout="wide")
    st.title("Dynamic Lane Allocation - Bangalore Toll Plazas")
    
    # Load data
    df = load_traffic_data()
    
    # Time slot selection
    col1, col2 = st.columns(2)
    with col1:
        selected_time = st.slider(
        "Select Time Slot (24-hour format)",
        min_value=time(0,0),
        max_value=time(23,59),
        value=time(8,0),
        step=timedelta(hours=1),  # Changed to timedelta type
        format="HH:mm"
    )
    
    # Convert time selection to hour
    selected_hour = selected_time.hour
    
    # Get counts for selected hour
    hourly_counts = df[df['hour'] == selected_hour].groupby(
        ['merchant_name', 'direction']).size().unstack(fill_value=0)
    
    # Plaza selection
    plazas = hourly_counts.index.tolist()
    selected_plaza = st.selectbox("Select Toll Plaza", plazas)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header(f"Traffic Data for {selected_time.strftime('%H:%M')}")
        plaza_data = hourly_counts.loc[selected_plaza]
        
        north_traffic = plaza_data.get('N', 0)
        south_traffic = plaza_data.get('S', 0)
        
        st.metric("Northbound Vehicles", north_traffic)
        st.metric("Southbound Vehicles", south_traffic)
        
        # Vehicle class distribution
        st.subheader("Vehicle Class Distribution")
        vehicle_counts = df[(df['merchant_name'] == selected_plaza) & 
                          (df['hour'] == selected_hour)][
                            'vehicle_class_code'].value_counts().reset_index()
        fig_pie = px.pie(vehicle_counts, names='vehicle_class_code', 
                        values='count', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    # Calculate lane allocation
    north_lanes, south_lanes = calculate_lane_allocation(north_traffic, south_traffic)
    
    with col2:
        st.header("Lane Allocation")
        st.metric("Total Lanes Available", 8)
        st.metric("Northbound Lanes Allocated", north_lanes)
        st.metric("Southbound Lanes Allocated", south_lanes)
        
        # Efficiency calculation
        base_delay = max(north_traffic/4, south_traffic/4)
        optimized_delay = max(north_traffic/north_lanes, south_traffic/south_lanes)
        efficiency_gain = ((base_delay - optimized_delay)/base_delay)*100
        st.metric("Estimated Efficiency Gain", f"{efficiency_gain:.1f}%")
    
    # Visualization
    st.header("Traffic Analysis")
    
    # Time-series analysis
    st.subheader(f"Daily Traffic Pattern ({selected_time.strftime('%H:%M')} highlighted)")
    hourly_trend = df[df['merchant_name'] == selected_plaza].groupby(
        ['hour', 'direction']).size().unstack().reset_index()
    fig_line = px.line(hourly_trend, x='hour', y=['N', 'S'], 
                      title="24-hour Traffic Trend",
                      labels={'value': 'Vehicles', 'hour': 'Hour of Day'})
    
    # Add vertical line for selected time
    fig_line.add_vline(x=selected_hour, line_dash="dash", 
                      line_color="red", annotation_text="Selected Time")
    st.plotly_chart(fig_line, use_container_width=True)

if __name__ == "__main__":
    main()
