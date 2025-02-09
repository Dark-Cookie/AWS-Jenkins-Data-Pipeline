import boto3
import pandas as pd
import pymysql
from io import StringIO
import awswrangler as wr
from botocore.exceptions import ClientError

s3_client = boto3.client('s3', region_name='ap-south-1')
rds_client = boto3.client('rds', region_name='ap-south-1')

bucket_name = 'my-s3-bucket-for-jenkins'
file_name = 'Data.csv'

response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
file_content = response['Body'].read().decode('utf-8')

data = pd.read_csv(StringIO(file_content))

def get_rds_endpoint(db_instance_id):
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_id)
        endpoint = response['DBInstances'][0]['Endpoint']['Address']
        return endpoint
    except ClientError as e:
        print(f"Error retrieving RDS endpoint: {e}")
        return None

def insert_data_to_rds(endpoint):
    try:
        conn = pymysql.connect(
            host=endpoint,
            user="${{ secrets.USERNAME }}",
            password="${{ secrets.PASSWORD }}",
            database="myrdsdb",
            port=3306,
        )

        cur = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS customer_data (
            CustomerID INT PRIMARY KEY,
            Genre VARCHAR(50),
            Age INT,
            `Annual_Income_(k$)` INT,
            Spending_Score INT
        );
        """
        cur.execute(create_table_query)

        for index, row in data.iterrows():
            cur.execute("""
                INSERT INTO customer_data (`CustomerID`, `Genre`, `Age`, `Annual_Income_(k$)`, `Spending_Score`)
                VALUES (%s, %s, %s, %s, %s)
            """, (row['CustomerID'], row['Genre'], row['Age'], row['Annual_Income_(k$)'], row['Spending_Score']))

        conn.commit()
        cur.close()
        conn.close()

        print("Data successfully transferred to RDS.")
        return True

    except pymysql.MySQLError as e:
        print(f"Error inserting data into RDS: {e}")
        return False


def push_data_to_glue():
    try:
        glue_database_name = 'my_glue_database'
        glue_table_name = 'customer_data'

        wr.s3.to_parquet(
            df=data,
            path=f"s3://{bucket_name}/glue-output/",
            dataset=True,
            database=glue_database_name,
            table=glue_table_name,
            mode="overwrite"
        )

        print(f"Data successfully transferred to Glue table: {glue_table_name}")

    except ClientError as e:
        print(f"Error pushing data to Glue: {e}")


def main():
    db_instance_id = 'database-1'
    
    rds_endpoint = get_rds_endpoint(db_instance_id)
    
    if rds_endpoint:
        success = insert_data_to_rds(rds_endpoint)

        if not success:
            print("Inserting to RDS failed, pushing data to Glue...")
            push_data_to_glue()
    else:
        print("RDS endpoint could not be retrieved. Pushing data to Glue...")
        push_data_to_glue()


if __name__ == '__main__':