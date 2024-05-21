from fetcher import ItemDataFetcher

# Ejemplo de uso
id_item = 4133 #Raydric Card
#id_item = 4098 #Dokebi Card
#id_item = 4126 #Minorous Card
#id_item = 985 #Elunium

id_item = 4133  # Raydric Card
fetcher = ItemDataFetcher(id_item)
fetcher.fetch_data()

