import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime
import numpy as np
from collections import OrderedDict


class ItemDataFetcher:
    def __init__(self, id_item):
        self.id_item = id_item
        self.base_url = "https://tools.payonstories.com/api/pc/history?id="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3"
        }
        self.sells_dataframe = pd.DataFrame(columns=["ds", "y"])
        self.vending_dataframe = pd.DataFrame(columns=["ds", "y"])
        self.hora_actualizacion = None

    def fetch_data(self):
        request_url = self.base_url + str(self.id_item)
        result = requests.get(request_url, headers=self.headers)
        data = result.json()
        self.hora_actualizacion = time.strftime(
            "%a, %d %b %Y %H:%M:%S +0000", time.gmtime((data["lastUpdated"] / 1000))
        )
        self._process_sells(data["sellHistory"])
        self._process_vending(data["vendHistory"])

        # Ordenar los DataFrames por la columna de fechas
        self.sells_dataframe = self.sells_dataframe.sort_values(by="ds").reset_index(
            drop=True
        )
        self.vending_dataframe = self.vending_dataframe.sort_values(
            by="ds"
        ).reset_index(drop=True)

    def _process_sells(self, sell_history):
        for sell_iterate in range(0, len(sell_history)):
            fecha = sell_history[sell_iterate]["x"]
            for sell_iterate_on_day in range(0, len(sell_history[sell_iterate]["y"])):
                precio_venta = sell_history[sell_iterate]["y"][sell_iterate_on_day]
                self.sells_dataframe = self.sells_dataframe._append(
                    {"ds": fecha, "y": precio_venta}, ignore_index=True
                )
        self.sells_dataframe["ds"] = pd.to_datetime(
            self.sells_dataframe["ds"]
        ).dt.tz_localize(
            None
        )  # Convertir a tz-naive
        self.sells_dataframe["y"] = self.sells_dataframe["y"].astype(float)

    def _process_vending(self, vend_history):
        for vending_iterate in range(0, len(vend_history)):
            fecha = vend_history[vending_iterate]["x"]
            for vending_iterate_on_day in range(
                0, len(vend_history[vending_iterate]["y"])
            ):
                precio_venta_ofrecido = vend_history[vending_iterate]["y"][
                    vending_iterate_on_day
                ]
                self.vending_dataframe = self.vending_dataframe._append(
                    {"ds": fecha, "y": precio_venta_ofrecido}, ignore_index=True
                )
        self.vending_dataframe["ds"] = pd.to_datetime(
            self.vending_dataframe["ds"]
        ).dt.tz_localize(
            None
        )  # Convertir a tz-naive
        self.vending_dataframe["y"] = self.vending_dataframe["y"].astype(float)

    def plot_data(self):
        plt.figure(figsize=(12, 6))
        plt.plot(self.sells_dataframe["ds"], self.sells_dataframe["y"], label="Ventas")
        plt.plot(
            self.vending_dataframe["ds"], self.vending_dataframe["y"], label="Vending"
        )
        plt.xlabel("Fecha")
        plt.ylabel("Precio")
        plt.title("Historial de Precios")
        plt.legend()
        plt.show()

    @classmethod
    def prepare_feature_matrix(cls, dataframe):
        rango_ventana = np.arange(1, 31)
        list_of_rows = []
        for current_index, row in dataframe.iterrows():
            if current_index + 31 > len(dataframe):
                break
            dict_info = OrderedDict(
                {
                    "precio": row["y"],
                    "fecha": row["ds"],
                    **{
                        f"t-{i}": dataframe.iloc[current_index + i]["y"]
                        for i in rango_ventana
                    },
                }
            )
            list_of_rows.append(dict_info)
        return pd.DataFrame(list_of_rows).iloc[::-1].reset_index(drop=True)
