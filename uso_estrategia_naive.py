import estrategia_naive as naive
import pandas as pd

df_cartas = naive.cargar_datos()
# restriccion temporal para no cargar todas las cartas
df_cartas = df_cartas.head(3)

df_resultados = naive.analizar_estrategia_naive_todas_las_cartas(df_cartas)
