import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Step 1: Connect to the database
conn = sqlite3.connect('ecommerce.db')

# Step 2: Load transactions into DataFrame
query = """
SELECT t.TransactionID, t.CustomerID, t.Quantity, t.UnitPrice, t.TransactionDate
FROM transactions t
INNER JOIN customers c ON t.CustomerID = c.CustomerID
"""
df = pd.read_sql_query(query, conn, parse_dates=['TransactionDate'])

# Step 3: Clean the data
df = df[df['Quantity'] > 0]
df['Total'] = df['Quantity'] * df['UnitPrice']

# Step 4: Create snapshot date
snapshot_date = df['TransactionDate'].max() + pd.Timedelta(days=1)

# Step 5: Calculate RFM metrics
rfm = df.groupby('CustomerID').agg({
    'TransactionDate': lambda x: (snapshot_date - x.max()).days,
    'TransactionID': 'count',
    'Total': 'sum'
}).rename(columns={
    'TransactionDate': 'Recency',
    'TransactionID': 'Frequency',
    'Total': 'Monetary'
})

# Step 6: Assign RFM scores with safe qcut
def get_scores(series, reverse=False):
    try:
        bin_obj = pd.qcut(series, q=5, duplicates='drop')
        labels = list(range(5, 0, -1)) if reverse else list(range(1, 6))
        return pd.qcut(series, q=5, labels=labels[:len(bin_obj.cat.categories)], duplicates='drop').astype(int)
    except ValueError:
        return pd.Series([3] * len(series), index=series.index)

rfm['R_Score'] = get_scores(rfm['Recency'], reverse=True)
rfm['F_Score'] = get_scores(rfm['Frequency'])
rfm['M_Score'] = get_scores(rfm['Monetary'])

rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

# Step 7: Segment customers based on RFM scores
def segment_customer(row):
    r, f = row['R_Score'], row['F_Score']
    if r >= 4 and f >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3:
        return 'Loyal Customers'
    elif r <= 2 and f <= 2:
        return 'At Risk'
    elif r <= 2 and f >= 3:
        return 'Cannot Lose'
    else:
        return 'Others'

rfm['Segment'] = rfm.apply(segment_customer, axis=1)

# Step 8: Print the RFM table
print("✅ RFM segmentation complete:\n")
print(rfm)

# Step 9: Save to CSV
rfm.to_csv("rfm_results.csv")
print("\n📁 RFM results saved to 'rfm_results.csv'")

# Step 10: Visualize segment counts
plt.figure(figsize=(8,5))
ax = rfm['Segment'].value_counts().plot(kind='bar', color='skyblue', edgecolor='black')
plt.title('Customer Segments')
plt.ylabel('Count')
plt.xticks(rotation=45)

# Add value labels
for p in ax.patches:
    ax.annotate(str(p.get_height()), (p.get_x() + 0.1, p.get_height() + 0.2))

plt.tight_layout()
plt.show()

# Close DB connection
conn.close()
