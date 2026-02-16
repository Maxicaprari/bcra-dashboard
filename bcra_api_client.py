#!/usr/bin/env python3
"""
Cliente para la API de Estadísticas del BCRA (Banco Central de Argentina)
Permite consultar principales variables económicas y monetarias
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import urllib3
from typing import Optional, List, Dict

# Suprimir warnings de SSL (común con APIs de gobierno argentino)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BCRAClient:
    """Cliente para interactuar con la API del BCRA"""
    
    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # APIs gov.ar suelen tener problemas de SSL
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_metodologia(self, id_variable: Optional[int] = None) -> Dict:
        """
        Obtiene la metodología de las variables
        
        Args:
            id_variable: ID de la variable específica (opcional)
            
        Returns:
            Diccionario con la metodología
        """
        if id_variable:
            url = f"{self.BASE_URL}/Metodologia/{id_variable}"
        else:
            url = f"{self.BASE_URL}/Metodologia"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_variables_monetarias(self, id_variable: Optional[int] = None, 
                                  desde: Optional[str] = None,
                                  hasta: Optional[str] = None) -> Dict:
        """
        Obtiene datos de variables monetarias
        
        Args:
            id_variable: ID de la variable específica (opcional)
            desde: Fecha desde en formato YYYY-MM-DD (opcional)
            hasta: Fecha hasta en formato YYYY-MM-DD (opcional)
            
        Returns:
            Diccionario con los datos
        """
        if id_variable:
            url = f"{self.BASE_URL}/Monetarias/{id_variable}"
        else:
            url = f"{self.BASE_URL}/Monetarias"
        
        params = {}
        if desde:
            params['desde'] = desde
        if hasta:
            params['hasta'] = hasta
            
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def listar_variables(self) -> pd.DataFrame:
        """
        Lista todas las variables disponibles con su descripción

        Returns:
            DataFrame con las variables disponibles
        """
        data = self.get_metodologia()

        if 'results' in data:
            df = pd.DataFrame(data['results'])
            if not df.empty:
                cols_disponibles = [c for c in ['idVariable', 'descripcion', 'nombreCorto'] if c in df.columns]
                return df[cols_disponibles] if cols_disponibles else df
        return pd.DataFrame()
    
    def get_datos_variable(self, id_variable: int,
                           dias_atras: int = 30) -> pd.DataFrame:
        """
        Obtiene datos de una variable específica

        Args:
            id_variable: ID de la variable
            dias_atras: Cantidad de días hacia atrás a consultar

        Returns:
            DataFrame con los datos de la variable
        """
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        fecha_desde = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')

        data = self.get_variables_monetarias(
            id_variable=id_variable,
            desde=fecha_desde,
            hasta=fecha_hasta
        )

        if 'results' in data:
            results = data['results']
            # La API devuelve los datos anidados en 'detalle'
            if isinstance(results, dict) and 'detalle' in results:
                df = pd.DataFrame(results['detalle'])
            elif isinstance(results, list) and len(results) > 0 and 'detalle' in results[0]:
                df = pd.DataFrame(results[0]['detalle'])
            else:
                df = pd.DataFrame(results)
            if not df.empty and 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
                df = df.sort_values('fecha')
            return df
        return pd.DataFrame()
    
    def get_multiple_variables(self, ids_variables: List[int], 
                               dias_atras: int = 30) -> Dict[int, pd.DataFrame]:
        """
        Obtiene datos de múltiples variables
        
        Args:
            ids_variables: Lista de IDs de variables
            dias_atras: Cantidad de días hacia atrás a consultar
            
        Returns:
            Diccionario con DataFrames por cada variable
        """
        resultados = {}
        
        for id_var in ids_variables:
            try:
                df = self.get_datos_variable(id_var, dias_atras)
                resultados[id_var] = df
            except Exception as e:
                print(f"Error al obtener variable {id_var}: {e}")
                resultados[id_var] = pd.DataFrame()
        
        return resultados


def main():
    """Función principal que consulta la API del BCRA"""
    bcra = BCRAClient()

    # 1. Listar todas las variables
    print("=" * 60)
    print("VARIABLES DISPONIBLES EN LA API DEL BCRA")
    print("=" * 60)
    try:
        variables = bcra.listar_variables()
        if not variables.empty:
            print(variables.head(10).to_string(index=False))
        else:
            print("No se pudieron obtener las variables.")
    except Exception as e:
        print(f"Error al listar variables: {e}")

    # 2. Obtener datos de Reservas Internacionales (ID: 1)
    print("\n" + "=" * 60)
    print("RESERVAS INTERNACIONALES (últimos 30 días)")
    print("=" * 60)
    try:
        reservas = bcra.get_datos_variable(id_variable=1, dias_atras=30)
        if not reservas.empty:
            print(reservas.tail(10).to_string(index=False))
            # Guardar a CSV
            reservas.to_csv('reservas_bcra.csv', index=False)
            print("\nDatos guardados en reservas_bcra.csv")
        else:
            print("No se obtuvieron datos de reservas.")
    except Exception as e:
        print(f"Error al obtener reservas: {e}")

    print("\n" + "=" * 60)
    print("Consulta finalizada.")


if __name__ == "__main__":
    main()