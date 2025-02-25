import streamlit as st
import pandas as pd
import numpy as np
from haversine import haversine
import plotly.express as px

# Load and preprocess data
@st.cache_data
def load_data():
    df = pd.read_csv('/Users/todankar/Desktop/traffic management/Bangalore_1Day_NETC.csv')
    
    # Extract coordinates
    df[['latitude', 'longitude']] = df['geocode'].str.split(',', expand=True).astype(float)
    
    # Parse datetime with error handling
    df['initiated_time'] = pd.to_datetime(df['initiated_time'], errors='coerce')
    df['hour'] = df['initiated_time'].dt.hour.fillna(-1).astype(int)
    
    return df

def calculate_congestion(df):
    """Calculate real-time congestion metrics with empty data handling"""
    try:
        congestion = df.groupby(['merchant_name', 'hour']).agg(
            total_traffic=('tag_id', 'count'),
            avg_processing_time=('inn_rr_time_sec', 'mean'),
            lanes_open=('lane', 'nunique')
        ).reset_index()
        
        congestion['congestion_level'] = np.where(
            congestion['total_traffic'] > 50, 
            'High', 
            np.where(congestion['total_traffic'] > 25, 'Medium', 'Low')
        )
        return congestion
    except Exception as e:
        st.error(f"Error calculating congestion: {str(e)}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="Geospatial Toll Routing", layout="wide")
    st.title("Bangalore Toll Plaza Traffic Management System")
    
    df = load_data()
    congestion_df = calculate_congestion(df)
    
    if df.empty or congestion_df.empty:
        st.error("No data available - please check your data source")
        return

    # Real-time Traffic Overview
    st.header("Real-time Toll Plaza Status")
    current_hour = pd.Timestamp.now().hour
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_plaza = st.selectbox("Select Toll Plaza", df['merchant_name'].unique())
    
    with col2:
        radius = st.slider("Search Radius (km)", 1, 10, 5)
    
    with col3:
        st.metric("Current Hour", current_hour)
    
    try:
        # Get plaza coordinates with error handling
        plaza_data = df[df['merchant_name'] == selected_plaza][['latitude', 'longitude']].iloc[0]
        current_location = (plaza_data['latitude'], plaza_data['longitude'])
    except IndexError:
        st.error("Selected plaza coordinates not found")
        return
    
    # Find nearby plazas with distance calculation
    try:
        df['distance'] = df.apply(lambda row: 
            haversine(current_location, (row['latitude'], row['longitude'])), axis=1)
        
        nearby_plazas = df[
            (df['distance'] <= radius) & 
            (df['merchant_name'] != selected_plaza)
        ]['merchant_name'].unique()
    except Exception as e:
        st.error(f"Error calculating distances: {str(e)}")
        nearby_plazas = []

    # Congestion analysis with empty state handling
    st.subheader("Load Balancing Suggestions")
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            current_status = congestion_df[
                (congestion_df['merchant_name'] == selected_plaza) &
                (congestion_df['hour'] == current_hour)
            ].iloc[0]
            
            st.metric("Current Plaza Traffic", 
                     f"{current_status['total_traffic']} vehicles/hr")
            st.metric("Average Processing Time", 
                     f"{current_status['avg_processing_time']:.1f} sec")
        except IndexError:
            st.warning("No traffic data available for current hour")
            current_status = None

    with col2:
        try:
            alt_plazas = congestion_df[
                (congestion_df['merchant_name'].isin(nearby_plazas)) &
                (congestion_df['hour'] == current_hour) &
                (congestion_df['congestion_level'] == 'Low')
            ]
            
            if not alt_plazas.empty:
                st.write("Recommended Alternative Plazas:")
                st.dataframe(alt_plazas[['merchant_name', 'total_traffic', 'congestion_level']], 
                            hide_index=True)
            else:
                st.warning("No less congested alternatives found within radius")
        except KeyError:
            st.warning("Could not load alternative plaza data")

    # Geospatial Visualization with error handling
    st.header("Live Traffic Map")
    try:
        map_df = df[['merchant_name', 'latitude', 'longitude']].drop_duplicates()
        current_hour_data = congestion_df[congestion_df['hour'] == current_hour]
        
        if not current_hour_data.empty:
            map_df = map_df.merge(current_hour_data, on='merchant_name')
            
            fig = px.scatter_mapbox(map_df,
                                  lat="latitude",
                                  lon="longitude",
                                  color="congestion_level",
                                  size="total_traffic",
                                  hover_name="merchant_name",
                                  zoom=10,
                                  color_discrete_map={'Low':'green', 'Medium':'yellow', 'High':'red'})
            
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No traffic data available for current hour")
    except Exception as e:
        st.error(f"Error generating map: {str(e)}")

    # Navigation Integration with error handling
    st.header("Adaptive Navigation Routing")
    try:
        if not alt_plazas.empty:
            destination = st.selectbox("Select Destination", 
                                    alt_plazas['merchant_name'].unique())
            
            try:
                dest_coords = df[df['merchant_name'] == destination][
                    ['latitude', 'longitude']].iloc[0]
                
                maps_link = f"""https://www.google.com/maps/dir/?api=1&origin={
                    current_location[0]},{current_location[1]}&destination={
                    dest_coords['latitude']},{dest_coords['longitude']}&travelmode=driving"""
                
                st.markdown(f"[Get Alternative Route via {destination}]({maps_link})")
            except IndexError:
                st.warning("Selected destination coordinates not found")
        else:
            st.info("No alternative routes available - all nearby plazas congested")
    except NameError:
        st.warning("Could not load navigation options")

if __name__ == "__main__":
    main()
