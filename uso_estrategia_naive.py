# Versión para EDA de la estrategia naive en el pasado
import estrategia_naive as naive
import pandas as pd
import time
import boto3
import numpy as np
from datetime import datetime

from parameters import (
    TIEMPO_SLEEP_ENTRE_CARTAS,
)


df_cartas = naive.cargar_datos()

all_cards_opportunities = pd.DataFrame()
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for card_id in df_cartas['ID']:
    print (card_id)
    try:
        mav, std, last_date_listed, cheaper_value, last_sell_price, mean_days_to_sell, opportunity = naive.detectar_oportunidad_una_carta(card_id)

    except Exception as e:
        print(f"Failed to process card {card_id}: {e}")
        mav, std, last_date_listed, cheaper_value, last_sell_price, mean_days_to_sell, opportunity = [None] * 7
    
    # Create a temporary DataFrame for the current card
    temp_df = pd.DataFrame({
        'ID': [card_id],
        'mav': [mav],
        'std': [std],
        'last_date_listed': [last_date_listed],
        'last_sell_price': [last_sell_price],
        'cheaper_value': [cheaper_value],
        'mean_days_to_sell': [mean_days_to_sell],
        'opportunity': [opportunity],
        'extracted_ts' : [timestamp]
    })

    all_cards_opportunities = pd.concat([all_cards_opportunities, temp_df], ignore_index=True)
    time.sleep(TIEMPO_SLEEP_ENTRE_CARTAS)

df_with_card_names = pd.merge(df_cartas, all_cards_opportunities, how = 'left', on = 'ID')

#para poder conectarlo correctamente con la base en athena, debe tener el formato del archivo que esta en athena 
# (esta parte no esta automática y todo se crea manual igual que los formatos a continuacion)

today_date = datetime.today().strftime('%Y-%m-%d')
df_with_card_names['extracted_date'] = today_date
df_with_card_names['mav'] = df_with_card_names['mav'].astype(np.float32)
df_with_card_names['std'] = df_with_card_names['std'].astype(np.float32)
df_with_card_names['last_sell_price'] = df_with_card_names['last_sell_price'].astype(np.float32)
df_with_card_names['cheaper_value'] = df_with_card_names['cheaper_value'].astype(np.float32)
df_with_card_names['mean_days_to_sell'] = df_with_card_names['mean_days_to_sell'].astype(np.float32)

# Convertir la columna de fecha a solo fecha (sin tiempo)
df_with_card_names['last_date_listed'] = pd.to_datetime(df_with_card_names['last_date_listed']).dt.date
df_with_card_names['opportunity'] = df_with_card_names['opportunity'].fillna(-1).astype(np.int32)

df_with_card_names.to_parquet('tmp/tmp.parquet', engine='pyarrow')


#esto esta muy feo pero debo salir del paso para leer las credentials
with open('/home/ubuntu/.aws/credentials') as file:
    next(file)
    # Read the next two lines
    key_id = file.readline().strip()
    access_key = file.readline().strip()
    
    # Get the part after '=' in each line
    key_id = key_id.split('=', 1)[1].strip()
    access_key = access_key.split('=', 1)[1].strip()

session = boto3.Session(
    aws_access_key_id=key_id,
    aws_secret_access_key=access_key
)

s3 = session.client('s3')
bucket_name = 'romillario-opportunities'
name_folder = 'opportunities_naive'
s3_file_path = f'{name_folder}/extracted_date={today_date}/df_opportunities_{today_date}.parquet'
s3.upload_file('tmp/tmp.parquet', bucket_name, s3_file_path)

athena_client = session.client('athena', region_name='us-east-1')

# Athena query parameters
athena_database = 'default'  # Replace with your database name
athena_table = 'opportunities_naive'        # Replace with your table name
output_location = 's3://romillario-opportunities/athena-results/'  # Set your Athena query result location

# Construct the query to add a partition
query = f"""
ALTER TABLE {athena_table}
ADD IF NOT EXISTS
PARTITION (extracted_date = '{today_date}')
LOCATION 's3://{bucket_name}/{name_folder}/extracted_date={today_date}/';
"""

# Execute the query
response = athena_client.start_query_execution(
    QueryString=query,
    QueryExecutionContext={
        'Database': athena_database
    },
    ResultConfiguration={
        'OutputLocation': output_location
    }
)

# Get query execution ID for tracking
query_execution_id = response['QueryExecutionId']
print(f"Athena query execution started. QueryExecutionId: {query_execution_id}")

while True:
    status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
    state = status['QueryExecution']['Status']['State']
    if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
        break
    print("Waiting for Athena query to complete...")
    time.sleep(5)

if state == 'SUCCEEDED':
    print("Partition added successfully.")
else:
    print(f"Query failed with state: {state}. Details: {status['QueryExecution']['Status']['StateChangeReason']}")

# Crear cliente Lambda #la region deberia estar en algun lado de parametro
lambda_client = session.client('lambda', region_name='us-east-1')

# Invocar la función Lambda
response = lambda_client.invoke(
    FunctionName='enviar_notificaciones',  # Reemplaza con el nombre de tu función Lambda
    InvocationType='Event'  # 'Event' hace que la invocación sea asíncrona
)

print(f"Lambda invocado: {response}")
print(f"Proceso completado exitosamente, hora inicio: {timestamp}")
