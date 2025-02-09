import boto3
import pandas as pd
import pymysql
from io import StringIO

# Initialize AWS S3 client
s3_client = boto3.client('s3', region_name='ap-south-1')

# S3 bucket and file information
bucket_name = 'my-s3-bucket-for-jenkins'
file_name = 'Data.csv'

# Fetch the file directly from S3 into memory (no local file storage)
response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
file_content = response['Body'].read().decode('utf-8')  # Read the file into memory

# Use pandas to read the CSV data from the string in memory
data = pd.read_csv(StringIO(file_content))


# Connect to RDS MySQL
conn = pymysql.connect(
    host="database-1.cpki20uu6y9i.ap-south-1.rds.amazonaws.com",
    user="admin",
    password="admin123",
    database="myrdsdb",
    port=3306,
)

# Create a cursor to execute SQL queries
cur = conn.cursor()

# SQL query to create the table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS customer_data (
    CustomerID INT PRIMARY KEY,
    Genre VARCHAR(50),
    Age INT,
    `Annual_Income_(k$)` INT,
    Spending_Score INT
);
"""

# Execute the table creation query
cur.execute(create_table_query)

# Iterate over the rows of the DataFrame and insert into the MySQL table
for index, row in data.iterrows():
    cur.execute("""
        INSERT INTO customer_data (`CustomerID`, `Genre`, `Age`, `Annual_Income_(k$)`, `Spending_Score`)
        VALUES (%s, %s, %s, %s, %s)
    """, (row['CustomerID'], row['Genre'], row['Age'], row['Annual_Income_(k$)'], row['Spending_Score']))


# Commit the transaction to save the data to the database
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()

print("Data successfully transferred to RDS.")