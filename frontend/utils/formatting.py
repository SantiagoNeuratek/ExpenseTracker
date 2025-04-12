import datetime
from typing import Any, Dict, List, Union
import pandas as pd


def format_currency(value: float) -> str:
    """
    Formatear un valor como moneda.

    Args:
        value: Valor numérico

    Returns:
        str: Valor formateado como moneda
    """
    return f"${value:.2f}"


def format_date(date: Union[str, datetime.date, datetime.datetime]) -> str:
    """
    Formatear una fecha.

    Args:
        date: Fecha a formatear

    Returns:
        str: Fecha formateada
    """
    if isinstance(date, str):
        try:
            date = datetime.datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            return date

    if isinstance(date, (datetime.date, datetime.datetime)):
        return date.strftime("%Y-%m-%d")

    return str(date)


def prepare_expenses_dataframe(
    expenses: List[Dict], categories: List[Dict] = None
) -> pd.DataFrame:
    """
    Preparar un DataFrame de pandas con los gastos formateados.

    Args:
        expenses: Lista de gastos
        categories: Lista de categorías para mapear IDs a nombres

    Returns:
        pd.DataFrame: DataFrame con los gastos formateados
    """
    if not expenses:
        return pd.DataFrame()

    # Crear DataFrame
    df = pd.DataFrame(expenses)

    # Convertir fechas
    if "date_incurred" in df.columns:
        df["date_incurred"] = pd.to_datetime(df["date_incurred"])

    # Mapear categorías
    if categories and "category_id" in df.columns and "category_name" not in df.columns:
        category_map = {cat["id"]: cat["name"] for cat in categories}
        df["category_name"] = df["category_id"].map(category_map)

    return df
