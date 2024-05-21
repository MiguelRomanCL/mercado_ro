import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

class ItemDataFetcher:
    def __init__(self, id_item):
        self.id_item = id_item
        self.base_url = "https://tools.payonstories.com/api/pc/history?id="
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3'}
        self.sells_dataframe = pd.DataFrame(columns=['Fecha', 'Precio'])
        self.vending_dataframe = pd.DataFrame(columns=['Fecha', 'Precio'])
        self.hora_actualizacion = None

    def fetch_data(self):
        request_url = self.base_url + str(self.id_item)
        result = requests.get(request_url, headers=self.headers)
        data = result.json()
        self.hora_actualizacion = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime((data['lastUpdated']/1000)))
        self._process_sells(data['sellHistory'])
        self._process_vending(data['vendHistory'])

    def _process_sells(self, sell_history):
        for sell_iterate in range(0, len(sell_history)):
            fecha = sell_history[sell_iterate]['x']
            for sell_iterate_on_day in range(0, len(sell_history[sell_iterate]['y'])):
                precio_venta = sell_history[sell_iterate]['y'][sell_iterate_on_day]
                self.sells_dataframe = self.sells_dataframe._append({'Fecha': fecha, 'Precio': precio_venta}, ignore_index=True)
        self.sells_dataframe['Fecha'] = pd.to_datetime(self.sells_dataframe['Fecha']).dt.date
        self.sells_dataframe['Precio'] = self.sells_dataframe['Precio'].astype(float)

    def _process_vending(self, vend_history):
        for vending_iterate in range(0, len(vend_history)):
            fecha = vend_history[vending_iterate]['x']
            for vending_iterate_on_day in range(0, len(vend_history[vending_iterate]['y'])):
                precio_venta_ofrecido = vend_history[vending_iterate]['y'][vending_iterate_on_day]
                self.vending_dataframe = self.vending_dataframe._append({'Fecha': fecha, 'Precio': precio_venta_ofrecido}, ignore_index=True)
        self.vending_dataframe['Fecha'] = pd.to_datetime(self.vending_dataframe['Fecha']).dt.date
        self.vending_dataframe['Precio'] = self.vending_dataframe['Precio'].astype(float)

    def plot_data(self):
        plt.figure(figsize=(12, 6))
        plt.plot(self.sells_dataframe['Fecha'], self.sells_dataframe['Precio'], label='Ventas')
        plt.plot(self.vending_dataframe['Fecha'], self.vending_dataframe['Precio'], label='Vending')
        plt.xlabel('Fecha')
        plt.ylabel('Precio')
        plt.title('Historial de Precios')
        plt.legend()
        plt.show()
