from fetcher import ItemDataFetcher
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import time

# Traerse la data
# id_item = 4133  # Raydric Card
# id_item = 1466  # Crescent Scythe
# id_item = 4133  # Raydric Card
id_item = 4035  # Hydra Card

# Cambiarlo por el json
ruta_cartas = "cards.json"
df_objetos = pd.read_json(ruta_cartas)


df_objetos = df_objetos.rename(columns={"Nombre": "Carta", "ID": "ID"})

threshold_porcentaje_compra = 0.7
porcentaje_ganancia_minima = 1.3
limite_espera_venta = 30


# Vamos a generar df con las compras y ventas para cada carta
list_of_dfs = []
for index_object, row_object in tqdm(df_objetos.iterrows(), total=len(df_objetos)):
    time.sleep(0.5)
    nombre_carta = row_object["Carta"]
    id_carta = row_object["ID"]

    fetcher = ItemDataFetcher(id_carta)
    fetcher.fetch_data()
    sells_dataframe = fetcher.sells_dataframe
    vending_dataframe = fetcher.vending_dataframe

    # Preprocesamiento para el modelo
    sells_df = sells_dataframe.sort_values(by="ds", ascending=False).reset_index(
        drop=True
    )
    listing_df = vending_dataframe.sort_values(by="ds", ascending=False).reset_index(
        drop=True
    )

    listing_df = listing_df.iloc[::-1].reset_index(drop=True)
    sells_df = sells_df.iloc[::-1].reset_index(drop=True)

    listing_df["MAV"] = listing_df["y"].rolling(window=7).mean()
    sells_df["MAV"] = sells_df["y"].rolling(window=7).mean()

    # Aquí sacamos la basura de los datos, ya que es poco probable que se pueda comprar o vender algo con menos del 10% del precio promedio. Hay valores muy pequeños que no tienen sentido.
    listing_df = listing_df.query("(y/MAV) >= 0.1").reset_index(drop=True)
    sells_df = sells_df.query("(y/MAV) >= 0.1").reset_index(drop=True)

    # Volvemos a calcular los MAV tras limpiar los datos, este es el MAV más confiable sobre el que nos basaremos para comprar y vender.
    listing_df["MAV"] = listing_df["y"].rolling(window=7).mean()
    sells_df["MAV"] = sells_df["y"].rolling(window=7).mean()

    listing_df.dropna(inplace=True)

    listing_df.reset_index(drop=True, inplace=True)

    listing_df["MAV"] = listing_df["MAV"].apply(lambda x: int(x))
    listing_df["y"] = listing_df["y"].apply(lambda x: int(x))
    listing_df["Buy_Point"] = np.where(
        listing_df["y"] < threshold_porcentaje_compra * listing_df["MAV"], 1, 0
    )

    list_of_rows = []
    # Revisamos los puntos donde queremos comprar
    for index, row in listing_df.query("Buy_Point == 1").iterrows():
        fecha_compra = row["ds"]
        precio_compra = row["y"]
        mav_compra = row["MAV"]

        # Luego miramos las fechas de venta posteriores a la fecha de compra y buscamos alguna venta que cumpla las condiciones buscadas.
        post_sells_df = sells_df.query("ds > @fecha_compra")
        for index_sells, row_sells in post_sells_df.iterrows():
            precio_venta = row_sells["y"]
            fecha_venta = row_sells["ds"]

            tiempo_transcurrido = (fecha_venta - fecha_compra).days

            # Quizás esto está demás, porque igual debemos venderla, pero la dejo como posible cambio de estrategia si pasa el periodo.
            if tiempo_transcurrido > limite_espera_venta:
                break

            valor_ganancia = precio_venta - precio_compra
            porcentaje_ganancia = valor_ganancia / precio_compra

            if porcentaje_ganancia > porcentaje_ganancia_minima:
                dict_info = {
                    "fecha_compra": fecha_compra,
                    "precio_compra": precio_compra,
                    "mav_compra": mav_compra,
                    "fecha_venta": fecha_venta,
                    "precio_venta": precio_venta,
                    "dias_transcurridos": tiempo_transcurrido,
                    "valor_ganancia": valor_ganancia,
                    "porcentaje_ganancia": porcentaje_ganancia,
                }
                list_of_rows.append(dict_info)
                break

    df = pd.DataFrame(list_of_rows)
    df.insert(0, "Carta", nombre_carta)
    df.insert(1, "ID", id_carta)
    list_of_dfs.append(df)

df_final = pd.concat(list_of_dfs)

df_final["ganancia_media_diaria"] = (
    df_final["valor_ganancia"] / df_final["dias_transcurridos"]
)
df_final["porcentaje_retorno"] = (
    100 * df_final["precio_venta"] / df_final["precio_compra"]
)


ts_analisis = "2024-04-01"
data_carta = df_final.query("fecha_compra >= @ts_analisis")

mean_dias_transcurridos = data_carta["dias_transcurridos"].mean()
mean_ganancia_diaria = data_carta["ganancia_media_diaria"].mean()
mean_porcentaje_retorno = data_carta["porcentaje_retorno"].mean()


df_summary = (
    df_final.query("fecha_compra >= @ts_analisis")
    .groupby("Carta")
    .agg(
        {
            "ID": "first",
            "dias_transcurridos": "mean",
            "ganancia_media_diaria": "mean",
            # "porcentaje_retorno": "mean",
            "fecha_compra": "min",
            "mav_compra": "count",
        }
    )
    # .sort_values(by="porcentaje_retorno", ascending=False)
    .rename(
        columns={
            "ID": "ID Carta",
            "dias_transcurridos": "Dias Transcurridos Promedio",
            "ganancia_media_diaria": "Ganancia Media Diaria",
            "fecha_compra": "Inicio Análisis",
            "mav_compra": "Cantidad_Operaciones",
        }
    )
)
df_summary["Ganancia Media Diaria"] = df_summary["Ganancia Media Diaria"].apply(
    lambda x: int(x)
)
