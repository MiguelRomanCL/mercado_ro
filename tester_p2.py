# %%
from fetcher import ItemDataFetcher
from prophet import Prophet
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

def evaluar_prediccion(fecha_analisis, periodo_prediccion=7):
    # Filtrar los datos hasta la fecha de análisis
    train_df = sells_max[sells_max['ds'] <= fecha_analisis].reset_index(drop=True)
    future_start_date = pd.to_datetime(fecha_analisis) + pd.Timedelta(days=1)
    future_end_date = future_start_date + pd.Timedelta(days=periodo_prediccion - 1)
    
    # Inicializar y ajustar el modelo
    model = Prophet()
    model.fit(train_df)
    
    # Crear DataFrame de futuro
    future = pd.date_range(start=future_start_date, end=future_end_date, freq='D')
    future = pd.DataFrame({'ds': future})
    
    # Realizar predicciones
    forecast = model.predict(future)
    
    # Unir las predicciones con los datos reales del conjunto de prueba
    test_df = sells_max[(sells_max['ds'] >= future_start_date) & (sells_max['ds'] <= future_end_date)].reset_index(drop=True)
    predictions = forecast[['ds', 'yhat']].merge(test_df[['ds', 'y']], on='ds', how='right')
    
    # Calcular métricas de evaluación
    mae = mean_absolute_error(predictions['y'], predictions['yhat'])
    mse = mean_squared_error(predictions['y'], predictions['yhat'])
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs((predictions['y'] - predictions['yhat']) / predictions['y'])) * 100
    std_error = np.std(predictions['y'] - predictions['yhat'])
    
    return mae, mse, rmse, mape, std_error, predictions

# Ejemplo de uso
id_item = 4133  # Raydric Card

fetcher = ItemDataFetcher(id_item)
fetcher.fetch_data()

sells_dataframe = fetcher.sells_dataframe
sells_max = sells_dataframe.groupby('ds').max().reset_index()

# %%
fechas_totales = sorted(sells_max['ds'].unique())

# %% [markdown]
# # Iterar sobre fechas totales

# %%
# Definir la fecha de análisis
fecha_analisis = '2024-05-01'

# Evaluar predicción
mae, mse, rmse, mape, std_error, predictions = evaluar_prediccion(fecha_analisis)

print(f"Resultados para la fecha de análisis {fecha_analisis}:")
print(f"MAE: {mae}")
print(f"MSE: {mse}")
print(f"RMSE: {rmse}")
print(f"MAPE: {mape}%")
print(f"STD Error: {std_error}")

# %%
# Gráfica de las predicciones vs valores reales
plt.figure(figsize=(12, 6))
plt.plot(predictions['ds'], predictions['y'], label='Valores Reales')
plt.plot(predictions['ds'], predictions['yhat'], label='Predicciones')
plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.title(f'Predicciones y Valores Reales a partir de {fecha_analisis}')
plt.legend()
plt.show()



