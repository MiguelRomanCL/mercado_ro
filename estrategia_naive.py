from fetcher import ItemDataFetcher
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
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


def cargar_datos(ruta="cards.json"):
    """Carga y renombra los datos desde un archivo JSON."""
    df = pd.read_json(ruta)
    df = df.rename(columns={"Nombre": "Carta", "ID": "ID"})
    return df


def obtener_datos_carta(id_carta):
    """Obtiene los datos de compra y venta para una carta dada."""
    fetcher = ItemDataFetcher(id_carta)
    fetcher.fetch_data()
    return fetcher.sells_dataframe, fetcher.listing_dataframe

def detectar_oportunidad_una_carta(id_carta):
    """Detectamos si hay una oportunidad con una estrategia que consiste en ver si el precio listado es muy bajo con respecto a un mav ajustado"""
    sells_df, listing_df = obtener_datos_carta(id_carta)

    #obtener mav y desviacion estandar con los ultimos valores de venta
    last_values_sold = sells_df.sort_values(by="ds", ascending=False).reset_index(drop=True)[0:LAST_VALUES_TO_CONSIDER]['y']
    removed_extremes = np.sort(last_values_sold)[1:-1] 
    mav = removed_extremes.mean()
    std = removed_extremes.std()

    #evaluar si el ultimo precio listado es conveniente segun el mav
    last_date_listed = listing_df.sort_values(by="ds", ascending=False).reset_index(drop=True)['ds'][0]
    cheaper_value = listing_df[listing_df['ds'] == last_date_listed].sort_values(by = 'y',ascending = True).reset_index(drop=True)['y'][0]
    opportunity_by_value = int(cheaper_value < mav - std)

    #evaluar si esta venta sería potencialmente una ganancia de acuerdo a la liquidez del item
    mean_days_to_sell = sells_df['ds'].diff().tail(7).reset_index(drop=True).apply(lambda x: float(x.days)).mean()
    ganancia_por_dia = (mav - cheaper_value)/mean_days_to_sell
    opportunity_by_ganancia = int(ganancia_por_dia > GANANCIA_BRUTA_DIARIA)
    opportunity = int(opportunity_by_value + opportunity_by_ganancia == 2)

    return mav, std, last_date_listed, cheaper_value, mean_days_to_sell, opportunity
