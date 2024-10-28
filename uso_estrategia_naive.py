# Versión para EDA de la estrategia naive en el pasado
import estrategia_naive as naive
import pandas as pd
import time
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
df_with_card_names.to_csv('test.csv', sep = ';')
