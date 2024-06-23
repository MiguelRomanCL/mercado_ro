# Versión para EDA de la estrategia naive en el pasado
import estrategia_naive as naive
import pandas as pd

df_cartas = naive.cargar_datos()
# restriccion temporal para no cargar todas las cartas
df_cartas = df_cartas.head(3)

df_resultados = naive.analizar_estrategia_naive_todas_las_cartas(df_cartas)


## También dejamos otro ejemplo de como analizar la información en tiempo real
# Versión para tiempo real
import estrategia_naive as naive

import pandas as pd
from parameters import TIEMPO_SLEEP_ENTRE_CARTAS
import time
from tqdm import tqdm

df_cartas = naive.cargar_datos()


# Configurar pandas para usar un formato específico en los números flotantes
# pd.set_option("display.float_format", "{:,.0f}".format)

df_cartas = df_cartas.head(10)

list_of_dfs = []
for index, carta in tqdm(df_cartas.iterrows(), total=df_cartas.shape[0]):
    id_carta = carta["ID"]
    nombre_carta = carta["Carta"]

    listing_df_enriched = naive.obtener_listing_df_con_info_sells(id_carta)
    last_date_ts = listing_df_enriched["ds"].max()
    listing_df_last = listing_df_enriched.query("ds == @last_date_ts").copy()
    listing_df_last["Carta"] = nombre_carta
    list_of_dfs.append(listing_df_last)


df = pd.concat(list_of_dfs).reset_index(drop=True)

# TODO: Revisar porqué hay casos con fecha_ultima_venta superior a la fecha actual
df["Dias_Transcurridos_tras_ultima_venta"] = (
    df["ds"] - df["fecha_ultima_venta"]
).dt.days
