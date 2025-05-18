# finance-bot/utils/date_utils.py
import dateparser
from datetime import datetime, timedelta
import re

def parse_date_to_str(date_input: str | None, default_to_today: bool = True) -> str | None:
    """
    Converte uma string de data (potencialmente em linguagem natural) para o formato YYYY-MM-DD.
    Retorna None se não conseguir parsear e default_to_today for False.
    """
    if not date_input:
        return datetime.now().strftime('%Y-%m-%d') if default_to_today else None
    
    date_input_lower = date_input.lower()
    if date_input_lower == 'hoje':
        return datetime.now().strftime('%Y-%m-%d')
    if date_input_lower == 'ontem':
        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Tenta parsear com dateparser, priorizando pt e formato DMY
    parsed_dt = dateparser.parse(date_input, languages=['pt'], settings={'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    
    if parsed_dt:
        return parsed_dt.strftime('%Y-%m-%d')
    
    # Fallback para formatos mais rígidos se dateparser falhar
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_input, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    return datetime.now().strftime('%Y-%m-%d') if default_to_today else None


def parse_period_to_dates(period_str: str) -> tuple[str | None, str | None, str]:
    """
    Converte uma string de período (ex: "mês passado", "julho", "julho de 2023")
    em datas de início e fim (YYYY-MM-DD) e uma descrição do período.
    Retorna (start_date, end_date, period_description_for_user).
    """
    now = datetime.now()
    period_str_lower = period_str.lower()
    period_description_for_user = period_str.capitalize() # Default description

    start_date_dt: datetime | None = None
    end_date_dt: datetime | None = None

    if "hoje" in period_str_lower:
        start_date_dt = end_date_dt = now
        period_description_for_user = "hoje"
    elif "ontem" in period_str_lower:
        start_date_dt = end_date_dt = now - timedelta(days=1)
        period_description_for_user = "ontem"
    elif "este mês" in period_str_lower or "mês atual" in period_str_lower:
        start_date_dt = now.replace(day=1)
        next_month_dt = (start_date_dt.replace(day=28) + timedelta(days=4))
        end_date_dt = next_month_dt - timedelta(days=next_month_dt.day)
        period_description_for_user = f"{now.strftime('%B de %Y').capitalize()}"
    elif "mês passado" in period_str_lower:
        first_day_current_month_dt = now.replace(day=1)
        last_day_last_month_dt = first_day_current_month_dt - timedelta(days=1)
        first_day_last_month_dt = last_day_last_month_dt.replace(day=1)
        start_date_dt = first_day_last_month_dt
        end_date_dt = last_day_last_month_dt
        period_description_for_user = f"{first_day_last_month_dt.strftime('%B de %Y').capitalize()}"
    else:
        parsed_dt_info = dateparser.parse(period_str, languages=['pt'], settings={'PREFER_DATES_FROM': 'past'})
        if parsed_dt_info:
            year_to_use = parsed_dt_info.year
            month_to_use = parsed_dt_info.month
            if not re.search(r'\d{4}', period_str) and \
               year_to_use == now.year and month_to_use > now.month:
                year_to_use -= 1
            start_date_dt = datetime(year_to_use, month_to_use, 1)
            next_month_calc_dt = (start_date_dt.replace(day=28) + timedelta(days=4))
            end_date_dt = next_month_calc_dt - timedelta(days=next_month_calc_dt.day)
            period_description_for_user = f"{start_date_dt.strftime('%B de %Y').capitalize()}"
        else:
            return None, None, f"Período '{period_str}' não reconhecido. Tente 'mês passado', 'este mês', 'Julho de 2023', etc."

    start_date_str = start_date_dt.strftime('%Y-%m-%d') if start_date_dt else None
    end_date_str = end_date_dt.strftime('%Y-%m-%d') if end_date_dt else None
            
    return start_date_str, end_date_str, period_description_for_user