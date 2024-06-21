from fetcher import ItemDataFetcher
import pandas as pd
import numpy as np
from collections import OrderedDict
import xgboost as xgb
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# Traerse la data
# id_item = 4133  # Raydric Card
# id_item = 1466  # Crescent Scythe
id_item = 4133  # Raydric Card
# id_item = 4035  # Hydra Card


fetcher = ItemDataFetcher(id_item)
fetcher.fetch_data()
sells_dataframe = fetcher.sells_dataframe
vending_dataframe = fetcher.vending_dataframe

# Preprocesamiento para el modelo
sell_dataframe_ordered = sells_dataframe.sort_values(by='ds', ascending=False).reset_index(drop=True).reset_index()
vending_dataframe_ordered = vending_dataframe.sort_values(by='ds', ascending=False).reset_index(drop=True).reset_index()

rango_ventana = np.arange(1, 31)

list_of_rows = []
for current_index, fila in sell_dataframe_ordered.iterrows():
    if current_index + 31 > len(sell_dataframe_ordered):
        break
    precio_en_t = fila['y']
    fecha_en_t = fila['ds']
    dict_info = OrderedDict()
    dict_info['precio'] = precio_en_t
    dict_info['fecha'] = fecha_en_t
    dict_info.update({
        f"t-{plus_index}": sell_dataframe_ordered.iloc[current_index + plus_index]["y"]
        for plus_index in rango_ventana
    })
    list_of_rows.append(dict_info)

df_procesado_wide = pd.DataFrame(list_of_rows)
df_procesado_wide = df_procesado_wide.iloc[::-1].reset_index(drop=True)

# Separar las características (X) y la variable objetivo (y)
X = df_procesado_wide.drop(columns=['precio', 'fecha'])
y = df_procesado_wide['precio']

# Dividir los datos en conjuntos de entrenamiento y prueba
proporcion_train = 0.95
n_train = int(len(df_procesado_wide) * proporcion_train)

X_train, X_test = X.iloc[:n_train], X.iloc[n_train:]
y_train, y_test = y.iloc[:n_train], y.iloc[n_train:]

# Crear y entrenar el modelo XGBoost
model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)

# Predecir y evaluar el modelo
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
mae = np.mean(abs(y_test- y_pred))
mape = np.mean(abs(y_test - y_pred) / y_test)
print(f"Mean Squared Error: {mse}")
print(f"Mean Absolute Error: {mae}")
print(f"Mean Absolute Percentage Error: {mape}")
# Mostrar una parte del DataFrame procesado
print(df_procesado_wide.head())

# Graficar los valores reales y predichos
plt.figure(figsize=(12, 6))
plt.plot(y_test.values, label='Valores Reales')
plt.plot(y_pred, label='Valores Predichos', linestyle='dashed')
plt.xlabel('Índice')
plt.ylabel('Precio')
plt.title('Comparación de Valores Reales y Predichos')
plt.legend()
plt.show()


y_train_pred = model.predict(X_train)
# Graficar los valores reales y predichos
plt.figure(figsize=(12, 6))
plt.plot(y_train, label='Valores Reales')
plt.plot(y_train_pred, label='Valores Predichos', linestyle='dashed')
plt.xlabel('Índice')
plt.ylabel('Precio')
plt.title('Comparación de Valores Reales y Predichos')
plt.legend()
plt.show()

#importancia variables

# Obtener la importancia de las características
importances = model.feature_importances_

# Crear un DataFrame para una mejor visualización
feature_importance_df = pd.DataFrame({
    'Feature': X_train.columns,
    'Importance': importances
})

# Ordenar el DataFrame por importancia
feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)
print(feature_importance_df)

# Crear un gráfico de barras
plt.figure(figsize=(10, 6))
plt.barh(feature_importance_df['Feature'], feature_importance_df['Importance'])
plt.xlabel('Importance')
plt.ylabel('Feature')
plt.title('Feature Importance')
plt.gca().invert_yaxis()  # Invertir el eje y para que la característica más importante aparezca arriba
plt.show()