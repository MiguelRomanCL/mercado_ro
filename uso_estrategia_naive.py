# Versión para EDA de la estrategia naive en el pasado
import estrategia_naive as naive
import pandas as pd
import numpy as np
from scipy import stats

from parameters import (
    PROP_MIN_MAV_VALID,
    PROP_MAX_MAV_VALID,
    PROP_UMBRAL_COMPRA,
    GANANCIA_BRUTA_MIN,
    GANANCIA_PORCENTUAL_MIN,
    MIN_PERIODS_STD,
    UMBRAL_STD_MULTI,
    DIAS_MAX_ESPERA,
    TIEMPO_SLEEP_ENTRE_CARTAS,
    LAST_VALUES_TO_CONSIDER,
    GANANCIA_BRUTA_DIARIA 
)


df_cartas = naive.cargar_datos()
# restriccion temporal para no cargar todas las cartas
df_cartas = df_cartas.head(3)

# Logica para 1 carta
card_id = df_cartas['ID'][0]
sells_df, listing_df = naive.obtener_datos_carta(card_id)
last_values_sold = sells_df.sort_values(by="ds", ascending=False).reset_index(drop=True)[0:LAST_VALUES_TO_CONSIDER]['y']
removed_extremes = np.sort(last_values_sold)[1:-1] 
mav = removed_extremes.mean()
std = removed_extremes.std()

last_date_listed = listing_df.sort_values(by="ds", ascending=False).reset_index(drop=True)['ds'][0]
cheaper_value = listing_df[listing_df['ds'] == last_date_listed].sort_values(by = 'y',ascending = True).reset_index(drop=True)['y'][0]
opportunity_by_value = int(cheaper_value < mav - std)


mean_days_to_sell = sells_df['ds'].diff().tail(7).reset_index(drop=True).apply(lambda x: float(x.days)).mean()
ganancia_por_dia = (mav - cheaper_value)/mean_days_to_sell
opportunity_by_ganancia = int(ganancia_por_dia > GANANCIA_BRUTA_DIARIA)
opportunity = int(opportunity_by_value + opportunity_by_ganancia == 2)
