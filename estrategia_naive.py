from fetcher import ItemDataFetcher
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
from parameters import (
    PROP_MIN_MAV_VALID,
    PROP_MAX_MAV_VALID,
    PROP_UMBRAL_COMPRA,
    GANANCIA_BRUTA_MIN,
    GANANCIA_PORCENTUAL_MIN,
    MIN_PERIODS_STD,
    UMBRAL_STD_MULTI,
    DIAS_MAX_ESPERA,
    TIEMPO_SLEEP_ENTRE_CARTAS,
)


def cargar_datos(ruta="cards.json"):
    """Carga y renombra los datos desde un archivo JSON."""
    df = pd.read_json(ruta)
    df = df.rename(columns={"Nombre": "Carta", "ID": "ID"})
    return df


def obtener_datos_carta(id_carta):
    """Obtiene los datos de compra y venta para una carta dada."""
    fetcher = ItemDataFetcher(id_carta)
    fetcher.fetch_data()
    return fetcher.sells_dataframe, fetcher.vending_dataframe


def eliminar_valores_extremos_inferiores(
    dataframe, umbral, columna_valor="y", columna_referencia="MAV"
):
    """Elimina los valores extremos inferiores basados en un umbral de la relación entre el valor y un valor de referencia."""
    condicion = f"({columna_valor}/{columna_referencia}) >= {umbral}"
    dataframe_filtrado = dataframe.query(condicion).reset_index(drop=True)
    return dataframe_filtrado


def eliminar_valores_extremos_superiores(
    dataframe, umbral, columna_valor="y", columna_referencia="MAV"
):
    """Elimina los valores extremos superiores basados en un umbral de la relación entre el valor y un valor de referencia."""
    condicion = f"({columna_valor}/{columna_referencia}) <= {umbral}"
    dataframe_filtrado = dataframe.query(condicion).reset_index(drop=True)
    return dataframe_filtrado


def procesar_datos(dataframe, columna_precio="y", umbral_std_multiplo=UMBRAL_STD_MULTI):
    """Procesa los datos realizando limpieza y cálculos necesarios, incluyendo STD y Lim_Inf siempre."""
    dataframe = dataframe.sort_values(by="ds", ascending=False).reset_index(drop=True)
    dataframe = dataframe.iloc[::-1].reset_index(drop=True)

    # Calcular MAV y preparar para eliminar valores extremos
    dataframe["MAV"] = dataframe[columna_precio].rolling(window=7, min_periods=1).mean()
    dataframe = eliminar_valores_extremos_inferiores(dataframe, PROP_MIN_MAV_VALID)
    dataframe = eliminar_valores_extremos_superiores(dataframe, PROP_MAX_MAV_VALID)

    # Recalcular MAV después de filtrar valores extremos
    dataframe["MAV"] = dataframe[columna_precio].rolling(window=7, min_periods=1).mean()

    dataframe["STD"] = (
        dataframe[columna_precio].rolling(window=7, min_periods=MIN_PERIODS_STD).std()
    )
    dataframe["UMBRAL_STD_MULTI"] = umbral_std_multiplo
    dataframe["Lim_Inf"] = dataframe["MAV"] - umbral_std_multiplo * dataframe["STD"]

    dataframe.dropna(inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    return dataframe


def cumple_condicion_venta(
    precio_compra,
    precio_venta,
    ganancia_bruta_min=GANANCIA_BRUTA_MIN,
    ganancia_porcentual_min=GANANCIA_PORCENTUAL_MIN,
):
    """
    Verifica si la venta cumple con la ganancia bruta mínima o con la ganancia porcentual mínima requerida.
    Ambos parámetros son opcionales y solo se evalúan si no son None.
    """
    ganancia_bruta = precio_venta - precio_compra
    ganancia_porcentual = ganancia_bruta / precio_compra

    condiciones = []

    # Agregar condición de ganancia bruta si el umbral es proporcionado
    if ganancia_bruta_min is not None:
        condiciones.append(ganancia_bruta >= ganancia_bruta_min)

    # Agregar condición de ganancia porcentual si el umbral es proporcionado
    if ganancia_porcentual_min is not None:
        condiciones.append(ganancia_porcentual >= ganancia_porcentual_min)

    # Evaluar si alguna de las condiciones se cumple
    cumple_condicion = any(condiciones) if condiciones else False

    return cumple_condicion, ganancia_bruta, ganancia_porcentual


def asignar_puntos_compra(
    dataframe, threshold_comprar_prop=None, diferencia_bruta_min=None
):
    """
    Asigna puntos de compra basados en umbrales proporcional, bruto y el límite inferior calculado,
    asegurando que el precio también debe estar por debajo del Lim_Inf.
    """
    condiciones = []

    # Agregar condición basada en el umbral proporcional si se proporciona
    if threshold_comprar_prop is not None:
        condiciones.append(dataframe["y"] < threshold_comprar_prop * dataframe["MAV"])

    # Agregar condición basada en la diferencia bruta si se proporciona
    if diferencia_bruta_min is not None:
        condiciones.append((dataframe["MAV"] - dataframe["y"]) >= diferencia_bruta_min)

    # Combinar condiciones anteriores con OR si existen múltiples condiciones
    if condiciones:
        condicion_final = condiciones[0]
        for cond in condiciones[1:]:
            condicion_final |= cond  # OR para combinar condiciones proporcional y bruta
    else:
        condicion_final = pd.Series([False] * len(dataframe), index=dataframe.index)

    # Aplicar condición de Lim_Inf como un filtro adicional con AND
    # Esto asegura que 'y' también debe estar por debajo de 'Lim_Inf'
    condicion_final &= dataframe["y"] < dataframe["Lim_Inf"]

    dataframe["Buy_Point"] = np.where(condicion_final, 1, 0)

    return dataframe


def identificar_oportunidades_venta(
    dataframe_compra,
    dataframe_venta,
    ganancia_bruta_min=GANANCIA_BRUTA_MIN,  # Valor por defecto definido globalmente
    ganancia_porcentual_min=GANANCIA_PORCENTUAL_MIN,  # Valor por defecto definido globalmente
    dias_max_espera=None,
):
    """Identifica oportunidades de venta para cada compra realizada."""
    resultados = []
    for index, compra in dataframe_compra[
        dataframe_compra["Buy_Point"] == 1
    ].iterrows():
        fecha_compra = compra["ds"]
        precio_compra = compra["y"]

        # Filtrar oportunidades de venta basadas en la fecha de compra
        oportunidades_venta = dataframe_venta[dataframe_venta["ds"] > fecha_compra]
        if dias_max_espera is not None:
            oportunidades_venta = oportunidades_venta[
                (dataframe_venta["ds"] - fecha_compra).dt.days <= dias_max_espera
            ]

        # Chequear cada oportunidad de venta
        for _, venta in oportunidades_venta.iterrows():
            cumple_condicion, ganancia_bruta, ganancia_porcentual = (
                cumple_condicion_venta(
                    precio_compra,
                    venta["y"],
                    ganancia_bruta_min,
                    ganancia_porcentual_min,
                )
            )
            if cumple_condicion:
                tiempo_espera_venta = (venta["ds"] - fecha_compra).days
                ganancia_media_diaria = ganancia_bruta / tiempo_espera_venta
                resultados.append(
                    {
                        "fecha_compra": fecha_compra,
                        "precio_compra": precio_compra,
                        "fecha_venta": venta["ds"],
                        "precio_venta": venta["y"],
                        "ganancia_bruta": ganancia_bruta,
                        "ganancia_porcentual": ganancia_porcentual,
                        "tiempo_espera_venta": tiempo_espera_venta,
                        "ganancia_media_diaria": ganancia_media_diaria,
                    }
                )
                break  # Salir después de encontrar la primera venta válida
    return pd.DataFrame(resultados)


def analizar_estrategia_naive_carta_especifica(id_carta):
    """Procesa una sola carta, retornando oportunidades de venta si existen."""
    # Obtener los dataframes de venta y compra para la carta
    sells_df, vending_df = obtener_datos_carta(id_carta)

    # Procesar los datos de compra y asignar puntos de compra
    processed_vending_df = procesar_datos(
        vending_df, columna_precio="y", umbral_std_multiplo=UMBRAL_STD_MULTI
    )
    processed_vending_df = asignar_puntos_compra(
        processed_vending_df,
        threshold_comprar_prop=PROP_UMBRAL_COMPRA,
        diferencia_bruta_min=GANANCIA_BRUTA_MIN,
    )

    # Procesar los datos de venta
    processed_sells_df = procesar_datos(
        sells_df, columna_precio="y", umbral_std_multiplo=UMBRAL_STD_MULTI
    )

    # Identificar oportunidades de venta
    oportunidades = identificar_oportunidades_venta(
        dataframe_compra=processed_vending_df,
        dataframe_venta=processed_sells_df,
        ganancia_bruta_min=GANANCIA_BRUTA_MIN,
        ganancia_porcentual_min=GANANCIA_PORCENTUAL_MIN,
        dias_max_espera=DIAS_MAX_ESPERA,
    )

    if not oportunidades.empty:
        oportunidades["ID"] = id_carta  # Agrega el ID de la carta para referencia
        return oportunidades
    else:
        return pd.DataFrame()  # Devolver un DataFrame vacío si no hay oportunidades


def analizar_estrategia_naive_todas_las_cartas(df_cartas):
    """Analiza todas las cartas proporcionadas y devuelve un DataFrame con todas las oportunidades de venta encontradas."""
    resultados_finales = []
    for _, carta in tqdm(df_cartas.iterrows(), total=len(df_cartas)):
        time.sleep(
            TIEMPO_SLEEP_ENTRE_CARTAS
        )  # Pausa configurada para evitar sobrecargar APIs o servicios externos
        df_oportunidades = analizar_estrategia_naive_carta_especifica(carta["ID"])

        if not df_oportunidades.empty:
            df_oportunidades["Carta"] = carta["Carta"]
            resultados_finales.append(df_oportunidades)

    if resultados_finales:
        df_resultados = pd.concat(resultados_finales, ignore_index=True)

        return df_resultados
    else:
        return (
            pd.DataFrame()
        )  # Devuelve un DataFrame vacío si no se encontraron oportunidades
