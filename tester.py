# %%
from fetcher import ItemDataFetcher
from prophet import Prophet
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Ejemplo de uso
id_item = 4133  # Raydric Card

fetcher = ItemDataFetcher(id_item)
fetcher.fetch_data()

sells_dataframe = fetcher.sells_dataframe

# Crear sells_max agrupando por fecha y tomando el máximo valor de 'y'
sells_max = sells_dataframe.groupby('ds').max().reset_index()

# Separar los datos en entrenamiento y prueba
split_date = '2024-05-01'  # por ejemplo, dividir en esta fecha
train_df = sells_max.query('ds <= @split_date').reset_index(drop=True)
test_df = sells_max.query('ds > @split_date').reset_index(drop=True)

print("Train DataFrame:")
print(train_df.tail())

print("Test DataFrame:")
print(test_df)

# Inicializar el modelo
model = Prophet()

# Ajustar el modelo a los datos de entrenamiento
model.fit(train_df)

# Calcular la cantidad de días futuros que necesitamos predecir
last_train_date = train_df['ds'].max()
last_test_date = test_df['ds'].max()
days_to_predict = (last_test_date - last_train_date).days

# Crear un DataFrame de futuro que incluya solo el período del conjunto de prueba
future = model.make_future_dataframe(periods=days_to_predict, freq='D', include_history=False)

# Predecir los valores futuros
forecast = model.predict(future)


# %%

# Unir las predicciones con las fechas originales del conjunto de prueba
predictions = forecast[['ds', 'yhat']].merge(test_df[['ds', 'y']], on='ds', how='right')

# Calcular métricas de evaluación
mae = mean_absolute_error(predictions['y'], predictions['yhat'])
mse = mean_squared_error(predictions['y'], predictions['yhat'])
rmse = mean_squared_error(predictions['y'], predictions['yhat'], squared=False)

print(f'MAE: {mae}')
print(f'MSE: {mse}')
print(f'RMSE: {rmse}')

# Gráfica de las predicciones vs valores reales
plt.figure(figsize=(12, 6))
plt.plot(train_df['ds'], train_df['y'], label='Entrenamiento')
plt.plot(test_df['ds'], test_df['y'], label='Prueba')
plt.plot(predictions['ds'], predictions['yhat'], label='Predicciones')
plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.title('Comparación de Predicciones y Valores Reales')
plt.legend()
plt.show()

# %%
