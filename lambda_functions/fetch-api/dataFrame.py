import json
import boto3
import pymysql

s3_client = boto3.client('s3')
rds_host = 'your-rds-endpoint'
rds_user = 'your-username'
rds_password = 'your-password'
rds_db = 'your-database'

def lambda_handler(event, context):
    sells_data = event.get('sells_data')
    listing_data = event.get('listing_data')
    
    # Guardamos los DataFrames en un bucket de S3
    s3_bucket = 'your-bucket-name'
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    
    sells_key = f'sells_data_{timestamp}.csv'
    listing_key = f'listing_data_{timestamp}.csv'
    
    s3_client.put_object(Body=sells_data, Bucket=s3_bucket, Key=sells_key)
    s3_client.put_object(Body=listing_data, Bucket=s3_bucket, Key=listing_key)
    
    # Conectamos a MySQL y guardamos el path y el timestamp
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )
    
    with connection.cursor() as cursor:
        insert_query = """
            INSERT INTO your_table (sells_path, listing_path, timestamp)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (sells_key, listing_key, timestamp))
        connection.commit()
    
    return {
        'statusCode': 200,
        'body': json.dumps('Data stored in S3 and paths saved in RDS')
    }
