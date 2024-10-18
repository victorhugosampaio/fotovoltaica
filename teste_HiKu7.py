import PySimpleGUI as sg
import numpy as np

import report_helper as report_helper
from single_diode_model import SingleDiodeModel
from table_data import obter_dados_data_hora, calcular_angulos_irradiancia


def HIKU7(canvas, data_selecionada, hora_selecionada, beta, gamma_p, lat, long_local, long_meridiano):
    # Dados do módulo solar HiKu7 Mono PERC 605 W
    short_circuit_current = 18.52  # [A]
    open_circuit_voltage = 41.5  # [V]
    temperature_current_coefficient = 0.05 / 100 * short_circuit_current  # ([%/ºC] / [100%]) * [A/ºC]
    series_resistance = 0.167  # Estimado (panel series resistance) 0.221
    shunt_resistance = 9.619  # Estimado (panel parallel (shunt) resistance) 415.405
    diode_quality_factor = 0.85  # Estimado 1.3

    number_of_series_connected_cells = 60  # Número de células em série

    number_of_voltage_decimal_digits = 1

    # Obter dados da tabela
    # data_selecionada = "11/01/2019"  # Substituir por qualquer data de interesse
    # hora_selecionada = "12:00"  # Substituir por qualquer hora de interesse

    try:
        dados_hora = obter_dados_data_hora(data_selecionada, hora_selecionada)

    except:
        sg.popup('Dados inseridos incorretos.', title='Erro')
        print('Dados inseridos incorretos!')

    if dados_hora is not None:
        # Obtendo valores da planilha
        operating_temperature = dados_hora['Temp_Cel'] + 273  # Convertendo para Kelvin
        actual_irradiance = dados_hora['Radiação']  # Irradiância obtida da tabela

        # print("Temperatura (ºC)", dados_hora['Temp_Cel'])
        temperatura_cel = dados_hora['Temp_Cel']

        # print("Irradiancia ", actual_irradiance)

        # Exemplo de cálculos com base nos dados obtidos
        angulos_irradiancia = calcular_angulos_irradiancia(
            data_hora_str=f'{data_selecionada} {hora_selecionada}',
            irradiancia_global=dados_hora['Radiação'],
            beta=beta,  # Inclinação do painel em relação ao plano horizontal (exemplo)
            gamma_p=gamma_p,  # Angulação do painel em relação ao norte ou sul
            lat=lat,  # Latitude da localização (exemplo)
            long_local=long_local,  # Longitude da localização (exemplo)
            long_meridiano=long_meridiano  # Meridiano central do fuso horário (exemplo: UTC-3, Brasil)
        )

        # Exibir informações calculadas
        # print("Ângulos e Irradiância:", angulos_irradiancia)

        # Criar o modelo de diodo simples com os dados do HiKu7
        single_diode_model = SingleDiodeModel(
            short_circuit_current,
            open_circuit_voltage,
            number_of_series_connected_cells,
            number_of_voltage_decimal_digits=number_of_voltage_decimal_digits,
            temperature_current_coefficient=temperature_current_coefficient,
            series_resistance=series_resistance,
            shunt_resistance=shunt_resistance,
            diode_quality_factor=diode_quality_factor
        )

        # Calculando os parâmetros baseados na irradiância e temperatura da tabela
        single_diode_model.calculate(operating_temperature, angulos_irradiancia['Irradiância Incidente'])

        # Gerando relatórios e gráficos para o modelo
        # report_helper.write_result_to_csv_file(single_diode_model, 'single_diode_model_hiku7_605W')
        report_helper.plot_result(single_diode_model, canvas)

        # Chama a função para gerar as curvas de tensão, corrente e potência
        # plt.show()

        # printar quantidade de paineis que devem ser utilizados
        potencia_gerada_modulo = max(single_diode_model.powers)  # Potência máxima gerada pelo módulo fotovoltaico
        potencia_desejada = dados_hora['Potencia_FV_Avg']  # Potência desejada obtida da tabela

        if potencia_gerada_modulo > 0:
            quantidade_paineis = potencia_desejada / potencia_gerada_modulo
            quantidade_paineis = np.ceil(quantidade_paineis)  # Arredonda para o próximo número inteiro
            # print(f"Potência desejada: {potencia_desejada:.2f} W")
            # print(f"Potência gerada por módulo: {potencia_gerada_modulo:.2f} W")
            # print(f"Quantidade de painéis necessários: {int(quantidade_paineis)}")
        else:
            print("A potência gerada pelo módulo é zero ou negativa.")


    else:
        print("Dados não encontrados para a data e hora selecionadas.")

    return (temperatura_cel, actual_irradiance, angulos_irradiancia, potencia_desejada, potencia_gerada_modulo,
            int(quantidade_paineis), short_circuit_current, open_circuit_voltage, temperature_current_coefficient,
            series_resistance, shunt_resistance, diode_quality_factor, number_of_series_connected_cells)
