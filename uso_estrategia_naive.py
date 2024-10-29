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
        'opportunity': [opportunity]
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
