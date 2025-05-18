import dateparser
from datetime import datetime, timedelta
import re

def parse_date_to_str(date_input: str | None, default_to_today: bool = True) -> str | None:
    """
    Converte uma string de data (potencialmente em linguagem natural ou vários formatos) 
    para o formato YYYY-MM-DD.
    Retorna None se não conseguir parsear e default_to_today for False (ou se o input for inválido).
    """
    if not date_input:
        return datetime.now().strftime('%Y-%m-%d') if default_to_today else None
    
    date_input_lower = date_input.lower().strip()
    now = datetime.now()

    if date_input_lower == 'hoje':
        return now.strftime('%Y-%m-%d')
    if date_input_lower == 'ontem':
        return (now - timedelta(days=1)).strftime('%Y-%m-%d')

    # Lista de formatos a serem tentados explicitamente ANTES do dateparser,
    # para maior controle, especialmente com anos de 2 dígitos.
    # Adicionar mais formatos conforme necessário.
    explicit_formats_with_year = [
        '%d/%m/%Y', '%d-%m-%Y', 
        '%d de %B de %Y', # 15 de maio de 2024 (requer locale ou dateparser)
        '%Y-%m-%d' # Formato ISO já é o desejado
    ]
    explicit_formats_without_year = [ # Assumirá o ano corrente
        '%d/%m', '%d-%m',
        '%d de %B' # 15 de maio (requer locale ou dateparser)
    ]

    parsed_dt: datetime | None = None

    # 1. Tentar formatos explícitos com ano
    for fmt in explicit_formats_with_year:
        try:
            # Para formatos com nome do mês, dateparser é melhor se não especificarmos locale
            if '%B' in fmt: 
                continue 
            parsed_dt = datetime.strptime(date_input, fmt)
            # Se o ano for de 2 dígitos e for interpretado como 19xx ou 20xx, verificar se faz sentido
            if parsed_dt.year < 2000 and len(str(parsed_dt.year)) == 4 and date_input.count('/') == 2 and len(date_input.split('/')[-1]) == 2 : # d/m/yy
                 parsed_dt = parsed_dt.replace(year=parsed_dt.year + 2000 if parsed_dt.year < 70 else parsed_dt.year + 1900) # Heurística comum para yy
            break 
        except ValueError:
            continue
    
    # 2. Se não parseou, tentar formatos explícitos sem ano (assumir ano corrente)
    if not parsed_dt:
        for fmt in explicit_formats_without_year:
            try:
                if '%B' in fmt:
                    continue
                dt_temp = datetime.strptime(date_input, fmt)
                parsed_dt = dt_temp.replace(year=now.year)
                # Se a data resultante for futura e o input não especificou ano, considerar ano passado
                if parsed_dt > now and not re.search(r'\b(de\s+)?\d{4}\b', date_input_lower):
                    # Verifique se o usuário não mencionou o ano
                    # e se a data DD/MM resultou em uma data futura no ano corrente.
                    # Isso é um pouco heurístico. dateparser lida melhor com isso.
                    # Para ser mais seguro, podemos deixar o dateparser tentar.
                    pass # Não vamos retroceder o ano aqui, deixaremos para o dateparser
                break
            except ValueError:
                continue

    # 3. Se ainda não parseou, usar dateparser como uma tentativa mais flexível
    # dateparser é bom com nomes de meses e formatos mais complexos.
    if not parsed_dt:
        # Configurações para o dateparser:
        # PREFER_DATES_FROM: 'past' - se ambíguo, prefere datas no passado.
        # DATE_ORDER: 'DMY' - ajuda a interpretar DD/MM/YYYY corretamente em pt-BR.
        # STRICT_PARSING: False - permite alguma flexibilidade.
        # FUZZY: True - pode ajudar com pequenas variações, mas use com cautela.
        settings = {'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}
        # Tentar remover preposições comuns que podem confundir o dateparser se ele não estiver esperando
        cleaned_date_input = date_input_lower.replace(' de ', ' ') 
        
        parsed_dt_dp = dateparser.parse(cleaned_date_input, languages=['pt'], settings=settings)
        
        if parsed_dt_dp:
            parsed_dt = parsed_dt_dp
            # Se dateparser não pegou o ano e resultou em data futura, e o input não tinha ano:
            # (Esta lógica pode ser redundante se 'PREFER_DATES_FROM': 'past' funcionar bem)
            if parsed_dt.year == now.year and parsed_dt > now and not re.search(r'\b(de\s+)?\d{4}\b', date_input_lower):
                # Check if the original input string explicitly mentioned a year
                # Heurística: se o input for "10 dezembro" e hoje é 1 nov, ele parseará para 10 dez do ano CORRENTE.
                # Se quisermos que "10 dezembro" seja do ano passado se já passou, precisamos de lógica adicional
                # ou confiar que o usuário será mais específico, ou que 'PREFER_DATES_FROM': 'past' resolverá.
                # Para inputs como "15/12" quando estamos em janeiro, dateparser com DMY e past deve pegar o ano passado.
                pass


    # 4. Se finalmente temos uma data parseada, formatar e retornar
    if parsed_dt:
        return parsed_dt.strftime('%Y-%m-%d')
    
    # 5. Se tudo falhou e default_to_today é True, retorna hoje
    if default_to_today:
        return now.strftime('%Y-%m-%d')
    
    # 6. Se tudo falhou e default_to_today é False, retorna None
    return None


def parse_period_to_dates(period_str: str) -> tuple[str | None, str | None, str]:
    """
    Converte uma string de período (ex: "mês passado", "julho", "julho de 2023")
    em datas de início e fim (YYYY-MM-DD) e uma descrição do período.
    Retorna (start_date, end_date, period_description_for_user).
    """
    now = datetime.now()
    period_str_lower = period_str.lower().strip()
    period_description_for_user = period_str.capitalize() 

    start_date_dt: datetime | None = None
    end_date_dt: datetime | None = None

    if not period_str_lower: # Período vazio, talvez retornar erro ou default
        return None, None, "Período não especificado."

    if "hoje" == period_str_lower:
        start_date_dt = end_date_dt = now
        period_description_for_user = "hoje"
    elif "ontem" == period_str_lower:
        start_date_dt = end_date_dt = now - timedelta(days=1)
        period_description_for_user = "ontem"
    elif "este mês" == period_str_lower or "mês atual" == period_str_lower:
        start_date_dt = now.replace(day=1)
        next_month_dt = (start_date_dt.replace(day=28) + timedelta(days=4))
        end_date_dt = next_month_dt - timedelta(days=next_month_dt.day)
        period_description_for_user = f"{now.strftime('%B de %Y').capitalize()}"
    elif "mês passado" == period_str_lower:
        first_day_current_month_dt = now.replace(day=1)
        last_day_last_month_dt = first_day_current_month_dt - timedelta(days=1)
        first_day_last_month_dt = last_day_last_month_dt.replace(day=1)
        start_date_dt = first_day_last_month_dt
        end_date_dt = last_day_last_month_dt
        period_description_for_user = f"{first_day_last_month_dt.strftime('%B de %Y').capitalize()}"
    elif "todo o período" == period_str_lower:
        start_date_dt, end_date_dt = None, None # Sinaliza para buscar tudo
        period_description_for_user = "todo o período"
    else:
        # Tenta parsear com dateparser, focando em mês/ano
        settings = {'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}
        # Limpar um pouco o input para dateparser
        cleaned_period_str = period_str_lower.replace(' de ', ' ')
        
        parsed_dt_info = dateparser.parse(cleaned_period_str, languages=['pt'], settings=settings)
        
        if parsed_dt_info:
            # Se dateparser retorna um dia específico, assumimos que o usuário quer o mês inteiro
            year_to_use = parsed_dt_info.year
            month_to_use = parsed_dt_info.month

            # Heurística para inferir o ano se apenas o mês foi dado e o mês é futuro
            # Ex: em Nov/2023, "Dezembro" deve ser Dez/2023, mas "Janeiro" deve ser Jan/2023 (passado)
            # Se o input original NÃO continha um ano:
            if not re.search(r'\b(de\s+)?\d{4}\b', period_str_lower):
                if year_to_use == now.year and month_to_use > now.month: # Mês futuro no ano corrente
                    # Esta lógica é complexa. PREFER_DATES_FROM: 'past' deve ajudar.
                    # Se for "julho" e estamos em maio, ele pegará julho do ano corrente.
                    # Se for "dezembro" e estamos em janeiro, ele DEVE pegar dezembro do ano passado.
                    pass # A configuração 'PREFER_DATES_FROM': 'past' deve cuidar disso.
                         # Se não, podemos forçar year_to_use -=1 em certos casos.

            start_date_dt = datetime(year_to_use, month_to_use, 1)
            next_month_calc_dt = (start_date_dt.replace(day=28) + timedelta(days=4))
            end_date_dt = next_month_calc_dt - timedelta(days=next_month_calc_dt.day)
            period_description_for_user = f"{start_date_dt.strftime('%B de %Y').capitalize()}"
        else:
            return None, None, f"Período '{period_str}' não reconhecido. Tente 'mês passado', 'este mês', 'Julho de 2023', etc."

    start_date_str = start_date_dt.strftime('%Y-%m-%d') if start_date_dt else None
    end_date_str = end_date_dt.strftime('%Y-%m-%d') if end_date_dt else None
            
    return start_date_str, end_date_str, period_description_for_user


if __name__ == '__main__':
    test_dates = [
        "hoje", "ontem", "15/05", "15/05/2024", "15-05-2024", "15 de maio", 
        "15 de maio de 2024", "2024-05-15", "12/04/24", "01/12", "dezembro",
        "natal", "amanhã", "próxima semana", "15/13/2023", None, ""
    ]
    print("--- Testando parse_date_to_str (default_to_today=True) ---")
    for date_str_test in test_dates:
        print(f"Input: '{date_str_test}' -> Output: '{parse_date_to_str(date_str_test)}'")
    
    print("\n--- Testando parse_date_to_str (default_to_today=False) ---")
    for date_str_test in test_dates:
        print(f"Input: '{date_str_test}' -> Output: '{parse_date_to_str(date_str_test, default_to_today=False)}'")

    print("\n--- Testando parse_period_to_dates ---")
    test_periods = ["hoje", "ontem", "este mês", "mês passado", "julho", "julho 2023", "dezembro", "janeiro", "todo o período", "bla"]
    for period_str_test in test_periods:
        s, e, d = parse_period_to_dates(period_str_test)
        print(f"Input: '{period_str_test}' -> Start: {s}, End: {e}, Desc: '{d}'")