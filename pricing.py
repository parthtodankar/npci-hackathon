import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Load and preprocess data
@st.cache_data
def load_data():
    df = pd.read_csv('/Users/todankar/Desktop/traffic management/Bangalore_1Day_NETC.csv')
    
    # Extract time from invalid dates
    df['initiated_time'] = pd.to_datetime(df['initiated_time'], errors='coerce').dt.time
    df['hour'] = pd.to_datetime(df['initiated_time'], format='%H:%M').dt.hour
    
    # Vehicle class base pricing
    base_prices = {
        'VC4': 50, 'VC5': 60, 'VC7': 75, 'VC9': 90,
        'VC10': 110, 'VC11': 130, 'VC12': 150, 'VC13': 170, 'VC20': 200
    }
    df['base_price'] = df['vehicle_class_code'].map(base_prices).fillna(50)
    
    return df

def calculate_congestion(df):
    # Calculate traffic density per hour per plaza
    congestion = df.groupby(['merchant_name', 'hour']).agg(
        traffic_count=('tag_id', 'count'),
        avg_speed=('inn_rr_time_sec', lambda x: np.mean(x) if not x.empty else 0)
    ).reset_index()
    
    # Handle edge cases before binning
    congestion = congestion.dropna(subset=['traffic_count'])
    
    # Modified qcut with error handling
    try:
        congestion['traffic_level'] = pd.qcut(congestion['traffic_count'], 
                                            q=5, 
                                            labels=[1, 2, 3, 4, 5],
                                            duplicates='drop')  # Key fix
    except ValueError as e:
        st.error(f"Quantile binning failed: {str(e)}")
        congestion['traffic_level'] = 3  # Fallback value
    
    return congestion

def dynamic_pricing(row, surge_multiplier):
    # Pricing logic based on traffic levels
    if row['traffic_level'] == 5:
        return 0  # Free during peak congestion
    elif row['traffic_level'] >= 3:
        return row['base_price'] * surge_multiplier
    else:
        return row['base_price']

def main():
    st.set_page_config(page_title="Dynamic Toll Pricing", layout="wide")
    st.title("Bangalore Toll Plaza Dynamic Pricing System")
    
    df = load_data()
    congestion_df = calculate_congestion(df)
    
    # User Controls
    col1, col2 = st.columns(2)
    with col1:
        surge_multiplier = st.slider("Surge Multiplier (Levels 3-4)", 1.2, 3.0, 1.8, 0.1)
    with col2:
        selected_plaza = st.selectbox("Select Toll Plaza", df['merchant_name'].unique())
    
    # Merge base prices with congestion data
    pricing_df = congestion_df.merge(
        df[['merchant_name', 'vehicle_class_code', 'base_price']].drop_duplicates(),
        on='merchant_name'
    )
    
    # Apply dynamic pricing
    pricing_df['dynamic_price'] = pricing_df.apply(
        lambda row: dynamic_pricing(row, surge_multiplier), axis=1
    )
    
    # Current Hour Analysis
    current_hour = pd.Timestamp.now().hour
    current_data = pricing_df[
        (pricing_df['merchant_name'] == selected_plaza) & 
        (pricing_df['hour'] == current_hour)
    ]
    
    st.header(f"Real-time Pricing - {selected_plaza}")
    
    if not current_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Traffic Level", current_data['traffic_level'].values[0])
        with col2:
            st.metric("Average Processing Time", f"{current_data['avg_speed'].values[0]:.1f} sec")
        with col3:
            st.metric("Dynamic Price Multiplier", f"{surge_multiplier}x")
    
    # Visualization
    st.subheader("24-Hour Pricing Schedule")
    
    # Heatmap for traffic levels
    fig1 = px.density_heatmap(
        pricing_df[pricing_df['merchant_name'] == selected_plaza],
        x='hour', y='vehicle_class_code', z='traffic_level',
        nbinsx=24, color_continuous_scale='Viridis',
        title="Traffic Level Heatmap (1=Low, 5=High)"
    )
    
    # Line chart for pricing
    fig2 = px.line(
        pricing_df[pricing_df['merchant_name'] == selected_plaza],
        x='hour', y='dynamic_price', color='vehicle_class_code',
        markers=True, title="Dynamic Pricing Trend"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
    
    # Pricing Table
    st.subheader("Detailed Pricing Matrix")
    pivot_df = pricing_df[pricing_df['merchant_name'] == selected_plaza].pivot_table(
        index='vehicle_class_code', columns='hour', 
        values='dynamic_price', aggfunc='mean'
    ).fillna(0).astype(int)
    
    st.dataframe(
        pivot_df.style.format("{:.0f}").background_gradient(cmap='YlOrRd'),
        use_container_width=True
    )
    
    # Pricing Logic Explanation
    st.markdown("""
    **Pricing Rules:**
    - Traffic Levels calculated using hourly quintiles
    - Dynamic Pricing Formula:
      - Level 5 (Peak): Free
      - Levels 3-4: Base Price × Surge Multiplier
      - Levels 1-2: Base Price
    - Base Prices by Vehicle Class:
      - VC4: ₹50 | VC5: ₹60 | VC7: ₹75 | VC9: ₹90
      - VC10: ₹110 | VC11: ₹130 | VC12: ₹150 | VC13: ₹170 | VC20: ₹200
    """)

if __name__ == "__main__":
    main()
