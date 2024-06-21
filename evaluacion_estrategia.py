# %%

from fetcher import ItemDataFetcher
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns

# Traerse la data
# id_item = 4133  # Raydric Card
# id_item = 1466  # Crescent Scythe
# id_item = 4133  # Raydric Card
id_item = 4035  # Hydra Card
id_item = 4217  # Enchanted Peach Tree Card


fetcher = ItemDataFetcher(id_item)
fetcher.fetch_data()
sells_dataframe = fetcher.sells_dataframe
vending_dataframe = fetcher.vending_dataframe

# Preprocesamiento para el modelo
sell_dataframe_ordered = sells_dataframe.sort_values(
    by="ds", ascending=False
).reset_index(drop=True)
vending_dataframe_ordered = vending_dataframe.sort_values(
    by="ds", ascending=False
).reset_index(drop=True)

vending_dataframe_ordered = sell_dataframe_ordered.copy()

vending_dataframe_ordered = vending_dataframe_ordered.iloc[::-1].reset_index(drop=True)

dataframe_processed = ItemDataFetcher.prepare_feature_matrix(fetcher.sells_dataframe)


vending_dataframe_ordered["MAV"] = (
    vending_dataframe_ordered["y"].rolling(window=7).mean()
)

vending_dataframe_ordered["Buy_Point"] = np.where(
    vending_dataframe_ordered["y"] < 0.7 * vending_dataframe_ordered["MAV"], 1, 0
)

porcentaje_ganancia_minima = 1.4

list_of_sell_points = [False] * len(
    vending_dataframe_ordered
)  # Inicializa la lista de puntos de venta con 'False'
precio_compra = None  # Inicializar el precio de compra

for index, row in vending_dataframe_ordered.iterrows():
    if row["Buy_Point"] == 1:
        precio_compra = row["y"]  # Actualizar el precio de compra en el punto de compra
    if precio_compra and row["y"] >= precio_compra * porcentaje_ganancia_minima:
        list_of_sell_points[index] = (
            True  # Marcar como punto de venta si se cumple la condición de ganancia
        )
        precio_compra = (
            None  # Resetear el precio de compra después de marcar un punto de venta
        )

vending_dataframe_ordered["Sell_Point"] = list_of_sell_points

vending_dataframe_ordered["Tiempo_Transcurrido"] = (
    vending_dataframe_ordered["ds"].diff().dt.days
)

vending_dataframe_ordered = vending_dataframe_ordered.iloc[::-1].reset_index(drop=True)

# %%
ts_inicio = "2024-05-01"
data = vending_dataframe_ordered.query("ds >= @ts_inicio")


# %%
fig, ax = plt.subplots(figsize=(15, 7))

sns.lineplot(data=data, x="ds", y="y", ax=ax, label="Sells")
sns.lineplot(data=data, x="ds", y="MAV", ax=ax, label="MAV")

vline = data.query("Buy_Point == 1")

for i in range(len(vline)):
    ax.axvline(x=vline.iloc[i]["ds"], color="red", linestyle="--")

vline_sell = data.query("Sell_Point == True")

for i in range(len(vline_sell)):
    ax.axvline(x=vline_sell.iloc[i]["ds"], color="green", linestyle="--")

# %%
