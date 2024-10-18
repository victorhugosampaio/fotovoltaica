from datetime import datetime
import pandas as pd
import numpy as np

# Defina a URL ou caminho do arquivo CSV
url = "https://docs.google.com/spreadsheets/d/1W1V5ExxROoVLTQAdsYKVv98rweN_bEoSwFwct9DN3Ao/gviz/tq?tqx=out:csv"

# Carregar a planilha com base na disponibilidade da URL ou caminho do arquivo
try:
    # Tente carregar a partir da URL
    df = pd.read_csv(url)
    # print(df)
except Exception as e:
    print(f"Não foi possível carregar os dados da URL: {e}. Tentando carregar do arquivo local.")

# Convertendo a coluna 'Data_Hora' para datetime, inferindo o formato e usando dayfirst=True
df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], format='%d/%m/%y %H:%M', dayfirst=True, errors='coerce')

# Convertendo colunas numéricas que estão como string (com vírgulas) para float
colunas_numericas = ['Radiação', 'Temp_Cel', 'Temp_Amb', 'Tensao_S1_Avg', 'Corrente_S1_Avg',
                     'Potencia_S1_Avg', 'Tensao_S2_Avg', 'Corrente_S2_Avg', 'Potencia_S2_Avg',
                     'Potencia_FV_Avg', 'Demanda_Avg', 'FP_FV_Avg', 'Tensao_Rede_Avg']

for coluna in colunas_numericas:
    df[coluna] = df[coluna].astype(str).str.replace(',', '.').astype(float)


# Função para obter dados de temperatura e irradiância da planilha
def obter_dados_data_hora(data_selecionada, hora_selecionada):
    # Converter a data e hora selecionadas para o formato datetime da coluna 'Data_Hora'
    data_hora_selecionada = pd.to_datetime(f"{data_selecionada} {hora_selecionada}", format='%d/%m/%y %H:%M')

    # Filtrar os dados com base na data e hora selecionada
    dados_hora = df[df['Data_Hora'] == data_hora_selecionada]

    if dados_hora.empty:
        print(f"Não há dados disponíveis para a data {data_selecionada} e hora {hora_selecionada}.")
        return None

    return dados_hora.iloc[0]


# Funções para conversão de ângulos
def deg_to_rad(deg):
    return deg * np.pi / 180


def rad_to_deg(rad):
    return rad * 180 / np.pi


# Função para calcular ângulos e irradiância baseada em dados
def calcular_angulos_irradiancia(data_hora_str, irradiancia_global, beta, gamma_p, lat, long_local, long_meridiano,
                                 horario_verao=0):
    # Convertendo a string da data e hora para objeto datetime
    data_hora = datetime.strptime(data_hora_str, "%d/%m/%y %H:%M")

    # Calculando o dia do ano
    dia = data_hora.timetuple().tm_yday

    # Determinando a equação do tempo (em horas)
    B = (360 / 365) * (dia - 81)
    EoT = 9.87 * np.sin(deg_to_rad(2 * B)) - 7.53 * np.cos(deg_to_rad(B)) - 1.5 * np.sin(deg_to_rad(B))
    EoT /= 60  # Convertendo para horas

    # Hora local
    hora_local = data_hora.hour + data_hora.minute / 60

    # Calculando a hora solar
    hora_solar = hora_local - ((long_local - long_meridiano) / 15) + EoT + horario_verao

    # Calculando a declinação solar
    declinacao_solar = 23.45 * np.sin(deg_to_rad(360 * (284 + dia) / 365))

    # Calculando o ângulo horário
    omega = 15 * (hora_solar - 12)

    # Calculando o ângulo zenital do sol
    theta_z = rad_to_deg(np.arccos(np.sin(deg_to_rad(lat)) * np.sin(deg_to_rad(declinacao_solar)) +
                                   np.cos(deg_to_rad(lat)) * np.cos(deg_to_rad(declinacao_solar)) * np.cos(
        deg_to_rad(omega))))

    # Calculando o azimute solar
    gamma_solar = rad_to_deg(np.arctan2(np.sin(deg_to_rad(omega)),
                                        (np.cos(deg_to_rad(omega)) * np.sin(deg_to_rad(lat)) -
                                         np.tan(deg_to_rad(declinacao_solar)) * np.cos(deg_to_rad(lat)))))

    # Cálculo do ângulo de incidência
    theta_i = rad_to_deg(
        np.arccos(np.sin(deg_to_rad(theta_z)) * np.cos(deg_to_rad(gamma_p - gamma_solar)) * np.sin(deg_to_rad(beta)) +
                  np.cos(deg_to_rad(theta_z)) * np.cos(deg_to_rad(beta))))

    # Cálculo da irradiância incidente usando a irradiância global e o ângulo de incidência
    G_inc = irradiancia_global * np.cos(deg_to_rad(theta_i))

    return {
        "Hora Solar": hora_solar,
        "Ângulo de Incidência": theta_i,
        "Irradiância Incidente": G_inc
    }
