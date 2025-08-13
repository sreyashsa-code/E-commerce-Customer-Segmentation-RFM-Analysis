import sqlite3
import pandas as pd

# Load CSV data
customers = pd.read_csv('data/customers.csv')
transactions = pd.read_csv('data/transactions.csv')

# Connect to SQLite DB
conn = sqlite3.connect('ecommerce.db')
customers.to_sql('customers', conn, if_exists='replace', index=False)
transactions.to_sql('transactions', conn, if_exists='replace', index=False)

print("Database created with 'customers' and 'transactions' tables.")
conn.close()
