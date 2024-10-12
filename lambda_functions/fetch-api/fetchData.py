import json
import requests
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    id_item = event.get('id_item')
    
    # Aseguramos que id_item esté presente
    if not id_item:
        return {
            'statusCode': 400,
            'body': json.dumps('id_item is missing')
        }

    fetcher = ItemDataFetcher(id_item)
    fetcher.fetch_data()
    
    # Convertimos los DataFrames a CSV para enviarlos
    sells_data = fetcher.sells_dataframe.to_csv(index=False)
    listing_data = fetcher.listing_dataframe.to_csv(index=False)
    
    payload = {
        'sells_data': sells_data,
        'listing_data': listing_data
    }
    
    # Invocación de la segunda Lambda
    try:
        response = lambda_client.invoke(
            FunctionName='your-second-lambda-function',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error invoking second Lambda: {str(e)}')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Data fetched and passed to second Lambda')
    }
