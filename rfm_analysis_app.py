# IMPORT IMPORTANT PACKAGES
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import streamlit as st

# SET PLOTLY DEFAULT TEMPLATE
pio.templates.default = "plotly_white"

# STREAMLIT HEADER AND INTRODUCTION
st.title('RFM Customer Segmentation Analysis for the Existing Customers')
st.write("""
    This app analyzes customer data using the RFM (Recency, Frequency, and Monetary) framework.
    Upload your CSV file containing customer purchase data to get started.
    The file should include columns for CustomerID, PurchaseDate, OrderID, and TransactionAmount.
""")

# Example of the required CSV format
st.write("### Example CSV File Format")
example_data = {
    'CustomerID': ['C001', 'C002', 'C001', 'C003', 'C002', 'C004', 'C001', 'C003', 'C005'],
    'PurchaseDate': ['2023-05-10', '2023-06-15', '2023-07-01', '2023-04-25', '2023-05-20', 
                     '2023-03-30', '2023-07-15', '2023-08-10', '2023-09-01'],
    'OrderID': ['O001', 'O002', 'O003', 'O004', 'O005', 'O006', 'O007', 'O008', 'O009'],
    'TransactionAmount': [150.75, 200.00, 350.00, 125.50, 180.00, 275.50, 120.00, 300.00, 95.00]
}
example_df = pd.DataFrame(example_data)
st.write(example_df)

st.write("""
    - **CustomerID**: Unique identifier for each customer.
    - **PurchaseDate**: Date when the purchase was made (format: YYYY-MM-DD).
    - **OrderID**: Unique identifier for each order, useful for counting frequency.
    - **TransactionAmount**: Monetary value of the purchase (numeric format).

    Ensure that your CSV file follows this structure for accurate analysis.
""")

# FILE UPLOAD
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write("Data Preview:", data.head())

    # Convert 'PurchaseDate' to datetime
    data['PurchaseDate'] = pd.to_datetime(data['PurchaseDate'])

    # Calculate Recency using today's date
    data['Recency'] = (pd.to_datetime(datetime.now()) - data['PurchaseDate']).dt.days

    # Calculate Frequency and Monetary Value
    frequency_data = data.groupby('CustomerID')['OrderID'].count().reset_index()
    frequency_data.rename(columns={'OrderID': 'Frequency'}, inplace=True)
    monetary_data = data.groupby('CustomerID')['TransactionAmount'].sum().reset_index()
    monetary_data.rename(columns={'TransactionAmount': 'MonetaryValue'}, inplace=True)
    
    # Merge Frequency and Monetary data back into the original dataframe
    data = data.merge(frequency_data, on='CustomerID', how='left')
    data = data.merge(monetary_data, on='CustomerID', how='left')

    # Define scoring criteria for each RFM value
    recency_scores = [5, 4, 3, 2, 1]
    frequency_scores = [1, 2, 3, 4, 5]
    monetary_scores = [1, 2, 3, 4, 5]

    # Function to handle qcut with fallback to cut
    def create_rfm_score(series, score_labels, q=5):
        # Use qcut if possible; fallback to cut if not enough unique values
        try:
            n_quantiles = min(q, series.nunique())
            if n_quantiles < q:
                return pd.cut(series, bins=n_quantiles, labels=score_labels[:n_quantiles]).astype(int)
            else:
                return pd.qcut(series, q=n_quantiles, labels=score_labels[:n_quantiles]).astype(int)
        except ValueError as e:
            st.error(f"Error in scoring: {e}")
            return pd.Series([0] * len(series))  # Return zero scores if there's an error

    # Assign RFM scores using the helper function
    data['RecencyScore'] = create_rfm_score(data['Recency'], recency_scores)
    data['FrequencyScore'] = create_rfm_score(data['Frequency'], frequency_scores)
    data['MonetaryScore'] = create_rfm_score(data['MonetaryValue'], monetary_scores)

    # Calculate the final RFM Score
    data['RFM_Score'] = data['RecencyScore'] + data['FrequencyScore'] + data['MonetaryScore']

    # Create RFM segments based on the RFM score
    segment_labels = ['Low-Value', 'Mid-Value', 'High-Value']
    data['Value Segment'] = pd.qcut(data['RFM_Score'], q=3, labels=segment_labels)

    # Assign RFM Customer Segments
    data['RFM Customer Segments'] = ''
    data.loc[data['RFM_Score'] >= 9, 'RFM Customer Segments'] = 'Champions'
    data.loc[(data['RFM_Score'] >= 6) & (data['RFM_Score'] < 9), 'RFM Customer Segments'] = 'Potential Loyalists'
    data.loc[(data['RFM_Score'] >= 5) & (data['RFM_Score'] < 6), 'RFM Customer Segments'] = 'At Risk Customers'
    data.loc[(data['RFM_Score'] >= 4) & (data['RFM_Score'] < 5), 'RFM Customer Segments'] = "Can't Lose"
    data.loc[(data['RFM_Score'] < 4), 'RFM Customer Segments'] = "Lost"

    # Show the RFM segmented data
    st.write("RFM Segmented Data:", data[['CustomerID', 'RFM Customer Segments']])

    # RFM Segment Distribution
    segment_counts = data['Value Segment'].value_counts().reset_index()
    segment_counts.columns = ['Value Segment', 'Count']

    # Create and show the bar chart for segment distribution
    fig_segment_dist = px.bar(segment_counts, x='Value Segment', y='Count',
                              color='Value Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                              title='RFM Value Segment Distribution')
    fig_segment_dist.update_layout(xaxis_title='RFM Value Segment', yaxis_title='Count', showlegend=False)
    st.plotly_chart(fig_segment_dist)
    
    st.write("""
        ### Interpretation of RFM Value Segment Distribution
        This bar chart shows the distribution of customers across three value segments:
        - **Low-Value**: Customers with a lower RFM score, indicating less recent purchases, lower frequency, or lower spending.
        - **Mid-Value**: Customers with average RFM scores.
        - **High-Value**: Customers with higher RFM scores, indicating more recent, frequent, or high-value transactions.

        **Decision Insight**: Focus marketing and retention efforts on High-Value customers to maintain their engagement.
        Analyze Low-Value customers to see if any can be nurtured into higher-value segments.
    """)

    # Treemap for RFM Customer Segments by Value
    segment_product_counts = data.groupby(['Value Segment', 'RFM Customer Segments']).size().reset_index(name='Count')
    fig_treemap_segment_product = px.treemap(segment_product_counts,
                                             path=['Value Segment', 'RFM Customer Segments'],
                                             values='Count',
                                             color='Value Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                                             title='RFM Customer Segments by Value')
    st.plotly_chart(fig_treemap_segment_product)
    
    st.write("""
        ### Interpretation of RFM Customer Segments Treemap
        This treemap shows the breakdown of customer segments like **Champions**, **Potential Loyalists**, etc., within each value segment.
        Larger areas represent more customers in that segment.

        **Decision Insight**: Use this visualization to identify segments with the most potential for growth, such as **Potential Loyalists** who might become **Champions**.
        Consider re-engaging **At Risk Customers** with targeted campaigns.
    """)

    # Filter the data to include only the customers in the Champions segment
    champions_segment = data[data['RFM Customer Segments'] == 'Champions']
    fig_box = go.Figure()
    fig_box.add_trace(go.Box(y=champions_segment['RecencyScore'], name='Recency'))
    fig_box.add_trace(go.Box(y=champions_segment['FrequencyScore'], name='Frequency'))
    fig_box.add_trace(go.Box(y=champions_segment['MonetaryScore'], name='Monetary'))

    fig_box.update_layout(title='Distribution of RFM Values within Champions Segment',
                          yaxis_title='RFM Value',
                          showlegend=True)
    st.plotly_chart(fig_box)
    
    st.write("""
        ### Interpretation of Champions Segment RFM Values
        This box plot shows the range and spread of Recency, Frequency, and Monetary scores within the **Champions** segment.
        - **Recency**: Lower values suggest more recent purchases.
        - **Frequency**: Higher values indicate more frequent purchases.
        - **Monetary**: Higher values indicate greater spending.

        **Decision Insight**: Understand which of your Champions purchase more frequently and spend the most.
        You can use this to tailor VIP programs or personalized offers.
    """)

    # Correlation Matrix of Champions
    correlation_matrix = champions_segment[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].corr()
    fig_heatmap = go.Figure(data=go.Heatmap(
                       z=correlation_matrix.values,
                       x=correlation_matrix.columns,
                       y=correlation_matrix.columns,
                       colorscale='RdBu',
                       colorbar=dict(title='Correlation')))
    fig_heatmap.update_layout(title='Correlation Matrix of RFM Values within Champions Segment')
    st.plotly_chart(fig_heatmap)
    
    st.write("""
        ### Interpretation of Correlation Matrix
        This heatmap displays correlations between Recency, Frequency, and Monetary values within the **Champions** segment.
        - A positive correlation means that as one value increases, the other tends to increase.
        - A negative correlation indicates that as one value increases, the other tends to decrease.

        **Decision Insight**: Use this to understand the relationship between purchase frequency and spending. 
        For example, if Frequency and Monetary are highly correlated, focusing on increasing purchase frequency could directly boost revenue.
    """)

    # Comparison of RFM Segments with grouped bar chart
    segment_scores = data.groupby('RFM Customer Segments')[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].mean().reset_index()
    fig_segment_scores = go.Figure()

    # Add bars for each score type
    for score, color in zip(['RecencyScore', 'FrequencyScore', 'MonetaryScore'], 
                            ['rgb(158,202,225)', 'rgb(94,158,217)', 'rgb(32,102,148)']):
        fig_segment_scores.add_trace(go.Bar(
            x=segment_scores['RFM Customer Segments'],
            y=segment_scores[score],
            name=score,
            marker_color=color
        ))

    # Update layout of the bar chart
    fig_segment_scores.update_layout(
        title='Comparison of RFM Segments based on Recency, Frequency, and Monetary Scores',
        xaxis_title='RFM Segments',
        yaxis_title='Score',
        barmode='group',
        showlegend=True
    )
    st.plotly_chart(fig_segment_scores)
    
    st.write("""
        ### Interpretation of RFM Segments Comparison
        This bar chart compares the average Recency, Frequency, and Monetary scores across different customer segments.
        - **Champions** tend to have low Recency scores (more recent), high Frequency, and high Monetary values.
        - **At Risk** customers might have higher Recency (less recent) but varying Frequency and Monetary values.

        **Decision Insight**: Use this chart to tailor your marketing strategies. For example, re-engaging **At Risk Customers** or providing special offers to **Potential Loyalists**.
    """)

else:
    st.write("Please upload a CSV file to analyze the RFM data.")
