# def write_result_to_csv_file(model, model_name):
#     import csv

#     file_name = generate_result_file_name(model_name, 'csv')
#     with open(file_name, 'w') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(['voltage', 'current', 'power'])
#         for i in range(len(model.voltages)):
#             writer.writerow([model.voltages[i], model.currents[i], model.powers[i]])

# def plot_result(model):
#     import matplotlib.pyplot as pyplot

#     pyplot.plot(model.voltages, model.currents)
#     pyplot.xlabel('Voltage [V]')
#     pyplot.ylabel('Current [A]')
#     pyplot.title('I-V curve')
#     pyplot.show(block=False)

#     pyplot.figure()
#     pyplot.plot(model.voltages, model.powers)
#     pyplot.xlabel('Voltage [V]')
#     pyplot.ylabel('Power [W]')
#     pyplot.title('P-V curve')
#     pyplot.show()

# def generate_result_file_name(model_name, file_extension):
#     from datetime import datetime
#     return model_name + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.' + file_extension

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from funcao import draw_figure


def write_result_to_csv_file(model, model_name):
    import csv

    file_name = generate_result_file_name(model_name, 'csv')
    with open(file_name, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['voltage', 'current', 'power'])
        for i in range(len(model.voltages)):
            writer.writerow([model.voltages[i], model.currents[i], model.powers[i]])


def plot_result(model, canvas):
    # Criação do gráfico com dois eixos Y
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Plot I-V: Tensão (V) vs Corrente (I)
    ax1.set_xlabel('Tensão (V)')
    ax1.set_ylabel('Corrente (A)', color='blue')
    ax1.plot(model.voltages, model.currents, color='blue', label="I-V curve")
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(0, max(model.currents) * 1.1)

    # Eixo secundário para a potência
    ax2 = ax1.twinx()
    ax2.set_ylabel('Potência (W)', color='green')
    ax2.plot(model.voltages, model.powers, color='green', label="P-V curve")
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.set_ylim(0, max(model.powers) * 1.1)

    # Marcador para o ponto de potência máxima
    idx_max_power = np.argmax(model.powers)
    v_max_power = model.voltages[idx_max_power]
    p_max_power = model.powers[idx_max_power]
    ax2.scatter(v_max_power, p_max_power, color='red', marker='x', s=100, label=f"Pmax = {p_max_power:.2f} W")

    # Adicionar legendas
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    # Personalização do título e grade
    plt.title('Curva I-V e P-V do Módulo Fotovoltaico')
    ax1.grid(True)

    # Exibir o gráfico
    # plt.show()
    plt.tight_layout()
    draw_figure(canvas, fig)
    plt.close(fig)


def generate_result_file_name(model_name, file_extension):
    return model_name + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.' + file_extension
