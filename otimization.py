import numpy as np
from table_data import obter_dados_data_hora, calcular_angulos_irradiancia
import matplotlib.pyplot as plt

# Função para calcular a irradiância total ao longo do dia para uma inclinação e orientação específicas
def calcular_irradiancia_total_dia(data_selecionada, beta, gamma_p, lat, long_local, long_meridiano):
    irradiancia_total = 0
    # Passando por todas as horas do dia
    for hora in range(24):
        for minuto in range(0, 60, 1):  # Verificar a cada minuto
            hora_selecionada = f"{hora:02d}:{minuto:02d}"
            # print("hora_selecionada", hora_selecionada)
            dados_hora = obter_dados_data_hora(data_selecionada, hora_selecionada)
            if dados_hora is not None:
                actual_irradiance = dados_hora['Radiação']
                operating_temperature = dados_hora['Temp_Cel'] + 273  # Convertendo para Kelvin

                angulos_irradiancia = calcular_angulos_irradiancia(
                    data_hora_str=f"{data_selecionada} {hora_selecionada}",
                    irradiancia_global=actual_irradiance,
                    beta= beta,  # Inclinação do painel
                    gamma_p= gamma_p,  # Orientação do painel em relação ao norte
                    lat= lat,  # Latitude
                    long_local= long_local,  # Longitude
                    long_meridiano=long_meridiano  # Meridiano central do fuso horário
                )
                irradiancia_total += angulos_irradiancia['Irradiância Incidente']
    return irradiancia_total

# Função para otimizar a inclinação e orientação
def otimizar_inclinacao_orientacao(data_selecionada, lat, long_local, long_meridiano):
    melhor_inclinacao = 0
    melhor_orientacao = 0
    irradiancia_maxima = -np.inf

    # Ajustar as varreduras de ângulo e inclinação
    inclinacoes = np.arange(0, 91, 1)  # Varredura de inclinação de 0 a 90 graus (em intervalos de 15 graus)
    orientacoes = np.arange(-90, 91, 1)  # Varredura de orientação de -90 a 90 graus (em intervalos de 15 graus)

    resultados = np.zeros((len(inclinacoes), len(orientacoes)))

    for i, beta in enumerate(inclinacoes):
        for j, gamma_p in enumerate(orientacoes):
            irradiancia_total = calcular_irradiancia_total_dia(data_selecionada, beta, gamma_p, lat, long_local, long_meridiano)
            # print("atual beta", beta)
            # print("atual gama", gamma_p)
            resultados[i, j] = irradiancia_total

            if irradiancia_total > irradiancia_maxima:
                irradiancia_maxima = irradiancia_total
                melhor_inclinacao = beta
                melhor_orientacao = gamma_p

    print("--------------------------")
    print(f"Melhor inclinação: {melhor_inclinacao} graus")
    print(f"Melhor orientação: {melhor_orientacao} graus (em relação ao norte)")
    print(f"Irradiância total máxima: {irradiancia_maxima:.2f} W/m² ao longo do dia")

    return inclinacoes, orientacoes, resultados


# Função para plotar o gráfico de otimização
def plotar_resultados_irradiancia(inclinacoes, orientacoes, resultados):
    plt.figure(figsize=(10, 8))
    X, Y = np.meshgrid(orientacoes, inclinacoes)
    plt.contourf(X, Y, resultados, cmap="viridis", levels=20)
    plt.colorbar(label="Irradiância Total [W/m²]")
    plt.xlabel("Orientação [graus]")
    plt.ylabel("Inclinação [graus]")
    plt.title("Otimização da Inclinação e Orientação do Painel")
    plt.show()