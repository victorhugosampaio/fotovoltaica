import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from funcao import create_panel, animate


def draw_animate(canvas, figure):
    """Embed a Matplotlib figure inside a PySimpleGUI canvas."""
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def main():
    # Layout do PySimpleGUI
    layout = [
        [sg.Text("Inclinação norte/sul (0 a 89 graus):"), sg.InputText(default_text="30", key='angle_z')],
        [sg.Text("Inclinação horizontal (0 a 89 graus):"), sg.InputText(default_text="17", key='angle_x')],
        [sg.Button("Iniciar Animação"), sg.Button("Sair")],
        [sg.Canvas(key='-CANVAS-')]  # Canvas para embutir a animação
    ]

    window = sg.Window("Animação de Placa Solar", layout, finalize=True)
    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.Widget

    global panel, step, ani
    panel = create_panel()
    step = [1]  # Lista para manter referência mutável
    frames = 50
    ani = None

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Embutir a figura do Matplotlib no Canvas do PySimpleGUI
    figure_canvas_agg = draw_animate(canvas, fig)

    while True:
        event, values = window.read(timeout=10)  # Timeout para manter a GUI responsiva
        if event == sg.WINDOW_CLOSED or event == "Sair":
            break
        if event == "Iniciar Animação":
            try:
                angle_z = float(values['angle_z'])
                angle_x = float(values['angle_x'])

                if angle_z == 90 or angle_x == 90:
                    sg.popup(
                        "Ambas as inclinações não podem ser 90 graus ao mesmo tempo. Por favor, insira novos valores.")
                    continue

                # Reiniciar a animação
                ax.cla()  # Limpa o gráfico para a nova animação
                ani = FuncAnimation(
                    fig, animate, fargs=(angle_x, angle_z, panel, frames, ax, step),
                    frames=2 * frames + 1, interval=30, repeat=False
                )
                figure_canvas_agg.draw()  # Atualiza a figura embutida

            except ValueError:
                sg.popup("Por favor, insira valores válidos para os ângulos.")

    window.close()


# Chamada da função principal
main()
