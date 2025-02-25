# npci-hackathon

Video:
https://youtu.be/6QhpubXV22U

Pitch Deck
https://docs.google.com/presentation/d/1XCTK8Ki0c9nqK4f152O71pmM_UY2hCkSpsgdVTC2bTI/edit#slide=id.g339bc0b8c2f_0_70

Key features of this implementation:

Traffic Level Calculation:

Uses quintiles to divide traffic into 5 levels

Considers both transaction count and processing speed

Updates in real-time based on current hour data

Dynamic Pricing Model:

Configurable surge multiplier for high traffic periods

Vehicle-class specific base pricing

Free tolls during peak congestion (Level 5)

Visualization:

Interactive heatmap showing traffic levels

Line chart displaying price trends

Color-coded pricing matrix table

User Controls:

Adjustable surge multiplier

Plaza selection dropdown

Real-time metrics display

Data Handling:

Robust time parsing from invalid dates

Automatic base price assignment by vehicle class

Hourly aggregation of traffic patterns

To use this system:

Traffic levels are automatically calculated every hour

Prices adjust based on real-time congestion

Operators can adjust surge multipliers as needed

Visualizations update automatically with data changes

The system helps:

Reduce congestion through dynamic pricing

Maintain traffic flow during peak hours

Provide transparent pricing based on actual usage

Optimize toll revenue while encouraging off-peak usage
