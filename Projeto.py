import PySimpleGUI as sg
import pandas as pd
import matplotlib.pyplot as plt
from funcao import plot_hourly_data, calculate_solar_parameters, calcular_resultados, calcular_gasto_sem_painel, \
    calcular_payback, calcular_geracao_mensal, calcular_gasto_com_painel
from funcao import create_panel, animate, draw_animate
from matplotlib.animation import FuncAnimation
from teste_HiKu7 import HIKU7

# Carregar os dados
url = "https://docs.google.com/spreadsheets/d/1W1V5ExxROoVLTQAdsYKVv98rweN_bEoSwFwct9DN3Ao/gviz/tq?tqx=out:csv"
df = pd.read_csv(url)
df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], format='%d/%m/%y %H:%M')
df['Radiação'] = df['Radiação'].str.replace(',', '.').astype(float)
df['Temp_Cel'] = df['Temp_Cel'].str.replace(',', '.').astype(float)

dados_por_hora = 'Plotar Dados por Hora'
irradiancia_paines_inclinacao = 'Calcular Irradiância para\nPainéis com Inclinação'
potencias_tensoes_correntes = 'Calcular Potências, Tensões e Correntes'
info_painel = "Painel HIKU7 MONO PERC"
payback = "Calcular Payback"
otimizacao = "Melhores Valores Para Inclinação e Orientação"
sair = 'Sair'


def main_menu():
    menu_layout = [
        [sg.Text('Menu Principal', font=('Helvetica', 16), justification='center')],
        [sg.Push(), sg.Button(dados_por_hora, size=(25, 3)), sg.Push()],
        [sg.Push(), sg.Button(irradiancia_paines_inclinacao, size=(25, 3)), sg.Push()],
        [sg.Push(), sg.Button(potencias_tensoes_correntes, size=(25, 3)), sg.Push()],
        [sg.Push(), sg.Button(info_painel, size=(25, 3)), sg.Push()],
        [sg.Push(), sg.Button(payback, size=(25, 3)), sg.Push()],
        [sg.Push(), sg.Button(otimizacao, size=(25, 3)), sg.Push()],
        [sg.Push(), sg.Button(sair, size=(25, 2)), sg.Push()]
    ]

    window = sg.Window('Menu Principal', menu_layout, size=(400, 500))

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == sair:
            break
        elif event == dados_por_hora:
            hour_selection(window)
        elif event == irradiancia_paines_inclinacao:
            inclinação(window)
        elif event == potencias_tensoes_correntes:
            potencias_selection(window)
        elif event == info_painel:
            show_panel(window)
        elif event == payback:
            payback_menu(window)
        elif event == otimizacao:
            show_optimization(window)

    window.close()


def hour_selection(parent_window):
    hour_layout = [
        [sg.Frame('', [
            [sg.Text('Selecione a Hora:', justification='center')],
            [sg.Slider(range=(0, 23), default_value=12, orientation='h', key='-HOUR-', size=(40, 20),
                       enable_events=True)],
            [sg.Text('Selecione o Minuto:', justification='center')],
            [sg.Slider(range=(0, 59), default_value=30, orientation='h', key='-MINUTE-', size=(40, 20),
                       enable_events=True)],
            [sg.Button('Voltar')],
            [sg.Canvas(key='-CANVAS-', size=(800, 600))]
        ], element_justification='center')]
    ]

    hour_window = sg.Window('Plotar Dados por Hora', hour_layout, size=(850, 700), finalize=True)

    hour_window.Maximize()

    selected_hour = int(hour_window['-HOUR-'].DefaultValue)
    selected_minute = int(hour_window['-MINUTE-'].DefaultValue)
    plot_hourly_data(selected_hour, selected_minute, hour_window['-CANVAS-'].TKCanvas)

    while True:
        hour_event, hour_values = hour_window.read()

        if hour_event == sg.WINDOW_CLOSED:
            hour_window.close()
            parent_window.un_hide()  # Retorna ao menu principal
            break
        elif hour_event == 'Voltar':
            hour_window.close()
            parent_window.un_hide()  # Retorna ao menu principal
            break
        elif hour_event in ('-HOUR-', '-MINUTE-'):
            selected_hour = int(hour_values['-HOUR-'])
            selected_minute = int(hour_values['-MINUTE-'])
            plot_hourly_data(selected_hour, selected_minute, hour_window['-CANVAS-'].TKCanvas)


def inclinação(parent_window):
    layout = [
        [sg.Text('Digite a Data e Hora (yyyy-mm-dd HH:MM:SS):', justification='center')],
        [sg.InputText('2019-11-01 12:00:00', key='data_hora_input', size=(25, 1), justification='center')],
        [sg.Text('Inclinação do painel (0° a 89°):', justification='center'),
         sg.InputText('30', key='beta', size=(5, 1), justification='center'),
         sg.Text('Angulação do painel (0° a 89°):', justification='center'),
         sg.InputText('17', key='gamma_p', size=(5, 1), justification='center')],
        [sg.Text('Latitude:', justification='center'),
         sg.InputText('0', key='latitude', size=(5, 1), justification='center'),
         sg.Text('Longitude:', justification='center'),
         sg.InputText('-46.6', key='longitude', size=(5, 1), justification='center'),
         sg.Text('Meridiano Central:', justification='center'),
         sg.InputText('-45', key='meridiano', size=(5, 1), justification='center')],
        [sg.Button('Calcular', size=(10, 1)), sg.Button('Voltar', size=(10, 1))],
        [sg.Text('Resultados:', size=(40, 1), font=('Helvetica', 16), justification='center')],
        [sg.Text('', key='resultados', font=('Helvetica', 12)), sg.Canvas(key='-CANVAS-', size=(400, 300))]
    ]

    window_inc = sg.Window('Cálculo de Irradiância Solar', layout, element_justification='c', finalize=True)

    # Centralizar a janela na tela
    window_inc.Maximize()

    canvas_elem = window_inc['-CANVAS-']
    canvas = canvas_elem.Widget

    global panel, step
    panel = create_panel()
    step = [1]
    frames = 50

    # Configurar a figura e o eixo 3D
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Embutir a figura no Canvas
    figure_canvas_agg = draw_animate(canvas, fig)

    while True:
        event, values = window_inc.read(timeout=10)

        if event in (sg.WINDOW_CLOSED, 'Voltar'):
            window_inc.close()
            parent_window.un_hide()
            break

        if event == 'Calcular':
            try:
                # Processar os dados de entrada
                data_hora_str = values['data_hora_input']
                data_hora = pd.to_datetime(data_hora_str, format='%Y-%m-%d %H:%M:%S')

                selected_index = df[df['Data_Hora'] == data_hora].index[0]
                irradiancia_global = df['Radiação'].iloc[selected_index]

                beta = float(values['beta'])
                gamma_p = float(values['gamma_p'])
                lat = float(values['latitude'])
                long_local = float(values['longitude'])
                long_meridiano = float(values['meridiano'])

                hora_solar, theta_i, G_inc = calculate_solar_parameters(
                    data_hora, irradiancia_global, beta, gamma_p, lat, long_local, long_meridiano
                )

                # Exibir resultados na interface
                resultados = (
                    f'Data e Hora Local: {data_hora}\n\n'
                    f'Irradiância Global: {irradiancia_global} W/m²\n\n'
                    f'Hora Solar: {hora_solar:.2f} horas\n\n'
                    f'Ângulo de incidência: {theta_i:.2f} graus\n\n'
                    f'Irradiância incidente: {G_inc:.2f} W/m²\n'
                )
                window_inc['resultados'].update(resultados)

                # Atualizar a animação
                ax.cla()  # Limpar o eixo
                ani = FuncAnimation(
                    fig, animate, fargs=(gamma_p, beta, panel, frames, ax, step),
                    frames=2 * frames + 1, interval=30, repeat=False
                )

                # Redesenhar a figura embutida
                figure_canvas_agg.draw()

            except ValueError:
                sg.popup("Por favor, insira valores válidos para os ângulos.")
            except IndexError:
                window_inc['resultados'].update("Erro: Data e Hora não encontrada no dataset.")
            except Exception as e:
                window_inc['resultados'].update(f'Erro inesperado: {str(e)}')


def potencias_selection(parent_window):
    layout = [
        [sg.Text('Potência Média desejada Rede(W):'),
         sg.InputText(default_text='1000', key='Pmed', size=(5, 1), justification='center', enable_events=True)],
        [sg.Text('Fase entre Tensão e Corrente (Graus°):'),
         sg.InputText(default_text='180', key='Ang', size=(5, 1), justification='center', enable_events=True)],
        [sg.Text('Amplitude (Vp):'),
         sg.InputText(default_text='220', key='Amp', size=(5, 1), justification='center', enable_events=True)],
        [sg.Button('Plotar'), sg.Button('Voltar')],
        [sg.Canvas(key='-CANVAS-CUSTOM-', size=(800, 600)), sg.Text('', key='-RESULTADOS-', font=('Helvetica', 12))]
    ]

    # Criação da janela
    window = sg.Window('Interface Gráfica', layout, element_justification='c', finalize=True)
    window.Maximize()

    # Função para verificar se todos os campos têm valores válidos
    def are_valid_inputs(values):
        try:
            float(values['Pmed'])
            float(values['Ang'])
            float(values['Amp'])
            return True
        except ValueError:
            return False

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'Voltar':
            window.close()
            parent_window.un_hide()  # Retorna ao menu principal
            break

        # Verifica a validade dos inputs após qualquer mudança
        if event == "Plotar":
            if are_valid_inputs(values):
                Pmed = float(values['Pmed'])
                Ang = float(values['Ang'])
                Amp = float(values['Amp'])

                # Chama a função para calcular resultados
                canvas_widget = window['-CANVAS-CUSTOM-'].TKCanvas
                pt_max, pt_media, pt_min, media_pr, Vfv, pfv, amplitude_tensao, amplitude_corrente, pfv_max, pfv_min, pfv_media, amplitude_tensao_fotovoltaico, amplitude_corrente_fotovoltaico = calcular_resultados(
                    canvas_widget, Pmed, Amp, Ang)

                # Atualiza o texto dos resultados
                resultados_texto = (
                    "Informações sobre o controle:\n\n"
                    f"Potência total máxima Rede: {pt_max:.2f}\n"
                    f"Potência total mínima Rede: {pt_min:.2f}\n\n"
                    f"Média da potência total Rede: {pt_media:.2f}\n"
                    f"Média da potência reativa Rede: {media_pr:.2f}\n\n"
                    f"Amplitude máxima da tensão Rede: {amplitude_tensao:.2f}\n"
                    f"Amplitude máxima da corrente Rede: {amplitude_corrente:.2f}\n\n"
                    f"Potência fotovoltaica máxima: {pfv_max:.2f}\n"
                    f"Potência fotovoltaica mínima: {pfv_min:.2f}\n"
                    f"Média da potência fotovoltaica: {pfv_media:.2f}\n\n"
                    f"Amplitude máxima da tensão fotovoltaica: {amplitude_tensao_fotovoltaico:.2f}\n"
                    f"Amplitude máxima da corrente fotovoltaica: {amplitude_corrente_fotovoltaico:.2f}"
                )
                window['-RESULTADOS-'].update(resultados_texto)
            else:
                window['-RESULTADOS-'].update("Por favor, preencha todos os campos com valores numéricos válidos!")

    # Fechar a janela
    window.close()


# Função para mostrar a imagem do painel
def show_panel(parent_window):
    layout = [
        [sg.Text("HORA(HH:MM): "), sg.InputText('12:00', key='hora_input', size=(25, 1), justification='center')],

        [sg.Text('Inclinação do painel (0° a 89°):', justification='center'),
         sg.InputText('30', key='beta', size=(5, 1), justification='center'),
         sg.Text('Angulação do painel (0° a 89°):', justification='center'),
         sg.InputText('17', key='gamma_p', size=(5, 1), justification='center')],
        [sg.Text('Latitude:', justification='center'),
         sg.InputText('0', key='latitude', size=(5, 1), justification='center'),
         sg.Text('Longitude:', justification='center'),
         sg.InputText('-46.6', key='longitude', size=(5, 1), justification='center'),
         sg.Text('Meridiano Central:', justification='center'),
         sg.InputText('-45', key='meridiano', size=(5, 1), justification='center')],

        [sg.Button('Plotar'), sg.Button('Voltar')],
        [sg.Canvas(key='-CANVAS-CUSTOM-', size=(800, 600)), sg.Text('', key='-RESULTADOS-', font=('Helvetica', 12))],
    ]

    window = sg.Window('Painel HIKU7', layout, element_justification='c', finalize=True)
    window.Maximize()

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'Voltar':
            window.close()
            parent_window.un_hide()  # Retorna ao menu principal
            break
        elif event == "Plotar":
            data = '1/11/19'
            hora = values["hora_input"]

            beta = float(values['beta'])
            gamma_p = float(values['gamma_p'])
            lat = float(values['latitude'])
            long_local = float(values['longitude'])
            long_meridiano = float(values['meridiano'])

            canvas_widget = window['-CANVAS-CUSTOM-'].TKCanvas

            temperatura_cel, actual_irradiance, angulos_irradiancia, potencia_desejada, potencia_gerada_modulo, quantidade_paineis, short_circuit_current, open_circuit_voltage, temperature_current_coefficient, series_resistance, shunt_resistance, diode_quality_factor, number_of_series_connected_cells = HIKU7(
                canvas_widget, data, hora, beta, gamma_p, lat, long_local, long_meridiano)

            resultados_texto = (
                f"Informações Painel HIKU7:\n\n"
                f"Corrente de Curto-Circuito (A): {short_circuit_current:.2f}\n"
                f"Tensão em Circuito Aberto (V): {open_circuit_voltage:.2f}\n"
                f"Coeficiente de Temperatura de Corrente: {temperature_current_coefficient}\n"
                f"Resistência em Série (Ω): {series_resistance:.2f}\n"
                f"Resistência em Paralelo (Ω): {shunt_resistance:.2f}\n"
                f"Fator de Qualidade do Diodo: {diode_quality_factor:.2f}\n"
                f"Número de Células Conectadas em Série: {number_of_series_connected_cells:.2f}\n\n"

                f"Informações de acordo com Localização e inclinação do painel:\n\n"
                f"Hora da Medição: {hora}\n"
                f"Temperatura (°C): {temperatura_cel:.2f}\n"
                f"Irradiância Atual (W/m²): {actual_irradiance:.2f}\n"
                # f"Hora Solar: {angulos_irradiancia['Hora Solar']:.2f}\n"
                f"Ângulo de Incidência (°): {angulos_irradiancia['Ângulo de Incidência']:.2f}\n"
                f"Irradiância Incidente (W/m²): {angulos_irradiancia['Irradiância Incidente']:.2f}\n\n"

                f"Quantidade de Placas:\n\n"
                f"Potência Desejada (W): {potencia_desejada:.2f}\n"
                f"Potência Gerada pelo Módulo (W): {potencia_gerada_modulo:.2f}\n"
                f"Quantidade de Painéis: {quantidade_paineis:.2f}\n"

            )
            window['-RESULTADOS-'].update(resultados_texto)
    window.close()


def payback_menu(parent_window):
    layout = [
        [sg.Text('Custo Inicial do Sistema (R$):'), sg.InputText('15000', key='-CUSTO-')],
        [sg.Text('Potência do Sistema Solar (kW):'), sg.InputText('3', key='-POTENCIA-')],
        [sg.Text('Horas de Sol por Dia:'), sg.InputText('10', key='-HORAS_SOL-')],
        [sg.Text('Eficiência do Sistema (%):'), sg.InputText('80', key='-EFICIENCIA-')],
        [sg.Text('Tarifa de Energia Elétrica (R$/kWh):'), sg.InputText('0.70', key='-TARIFA-')],
        [sg.Text('Consumo Mensal Médio (kWh):'), sg.InputText('500', key='-CONSUMO-')],
        [sg.Button('Calcular'), sg.Button('Voltar')],
        [sg.Text('Resultados:', font=('Helvetica', 14))],
        [sg.Text('', key='-RESULTADOS-', size=(40, 10))]
    ]

    window = sg.Window('Calculadora de Payback', layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Voltar':
            window.close()
            parent_window.un_hide()  # Retorna ao menu principal
            break

        if event == 'Calcular':
            try:
                # Obter os valores dos campos de texto
                custo_inicial = float(values['-CUSTO-'])
                potencia_sistema = float(values['-POTENCIA-'])
                horas_sol_dia = float(values['-HORAS_SOL-'])
                eficiencia = float(values['-EFICIENCIA-']) / 100
                tarifa = float(values['-TARIFA-'])
                consumo_mensal = float(values['-CONSUMO-'])

                # Calcular geração mensal
                geracao_mensal = calcular_geracao_mensal(potencia_sistema, horas_sol_dia, eficiencia)

                # Calcular economia mensal e payback
                gasto_sem_painel = calcular_gasto_sem_painel(consumo_mensal, tarifa)
                gasto_com_painel = calcular_gasto_com_painel(geracao_mensal, consumo_mensal, tarifa)
                payback = calcular_payback(custo_inicial, -gasto_com_painel)

                # Atualizar os resultados na interface
                resultados_texto = (
                    f'Geração Mensal Estimada: {geracao_mensal:.2f} kWh\n'
                    f'Gasto Mensal Sem Painel: R$ {gasto_sem_painel:.2f}\n'
                    f'Gasto Mensal Com Painel: R$ {gasto_com_painel:.2f}\n'
                    f'Tempo de Payback: {payback:.1f} meses'
                )
                window['-RESULTADOS-'].update(resultados_texto)

            except ValueError:
                window['-RESULTADOS-'].update('Por favor, insira valores numéricos válidos.')

    window.close()

def show_optimization(parent_window):
    layout = [
        [sg.Column([[sg.Image(filename='figura_angulos_ideais.png')]]),
         sg.Column([[sg.Text('Melhor inclinação: 18 graus')],
                    [sg.Text('Melhor orientação: -12 graus (em relação ao norte)')],
                    [sg.Text('Irradiância total máxima: 285687.82 W/m² ao\nlongo do dia')]])],
        [sg.Button('Voltar')]
    ]
    
    info_window = sg.Window("Otimização", layout, modal=True)


    while True:
        event, values = info_window.read()
        if event == sg.WINDOW_CLOSED or event == 'Voltar':
            info_window.close()
            parent_window.un_hide()
            break


main_menu()
