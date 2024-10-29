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
        self.listing_dataframe = pd.DataFrame(columns=["ds", "y"])
        self.hora_actualizacion = None
        self.raw_data = None

    def fetch_data(self):
        request_url = self.base_url + str(self.id_item)
        proxy_df = self._process_proxies()
        for _,row in proxy_df.iterrows():
            proxy = {"http": row['proxy'], "https": row['proxy']}
            time.sleep(2)
            try:           
                result = requests.get(request_url, headers=self.headers, proxies=proxy, timeout=5)
            
                if result.status_code == 200:
                    print(f"Success with proxy {row['proxy']}")
                    data = result.json()
                    self.hora_actualizacion = time.strftime(
                        "%a, %d %b %Y %H:%M:%S +0000", time.gmtime((data["lastUpdated"] / 1000))
                    )
                    self._process_sells(data["sellHistory"])
                    self._process_listing(data["vendHistory"])
                
                            # Ordenar los DataFrames por la columna de fechas
                    self.sells_dataframe = self.sells_dataframe.sort_values(by="ds").reset_index(
                        drop=True
                    )
                    self.listing_dataframe = self.listing_dataframe.sort_values(
                        by="ds"
                    ).reset_index(drop=True)

                    self.raw_data = data
                    break
            except requests.RequestException as e:
                print(f"Failed with proxy {row['proxy']}: {e}")




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

    def _process_listing(self, vend_history):
        for vending_iterate in range(0, len(vend_history)):
            fecha = vend_history[vending_iterate]["x"]
            for vending_iterate_on_day in range(
                0, len(vend_history[vending_iterate]["y"])
            ):
                precio_venta_ofrecido = vend_history[vending_iterate]["y"][
                    vending_iterate_on_day
                ]
                self.listing_dataframe = self.listing_dataframe._append(
                    {"ds": fecha, "y": precio_venta_ofrecido}, ignore_index=True
                )
        self.listing_dataframe["ds"] = pd.to_datetime(
            self.listing_dataframe["ds"]
        ).dt.tz_localize(
            None
        )  # Convertir a tz-naive
        self.listing_dataframe["y"] = self.listing_dataframe["y"].astype(float)

    def _process_proxies(self):
        "el filtro es solo de US y http y formato json: https://proxyscrape.com/free-proxy-list"
        link_free_proxy = 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=http&country=us&proxy_format=protocolipport&format=json&timeout=20000'
        proxy_list = requests.get(link_free_proxy)
        proxy_json = proxy_list.json()
        # Extract relevant fields from each proxy
        proxy_data = [
            {
                "alive": proxy.get("alive"),
                "alive_since": proxy.get("alive_since"),
                "port": proxy.get("port"),
                "protocol": proxy.get("protocol"),
                "proxy": proxy.get("proxy"),
                "ip": proxy.get("ip")
            }
            for proxy in proxy_json.get("proxies", [])
        ]

        #limito a maximo 30 proxys, solo para no iterar sobre una posible lista gigante
        proxy_df = pd.DataFrame(proxy_data).sort_values(by ='alive_since', ascending = False).reset_index(drop=True).head(30)
        
        return proxy_df
        


