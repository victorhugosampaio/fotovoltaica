import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Carregar os dados para a primeira funcionalidade
url = "https://docs.google.com/spreadsheets/d/1W1V5ExxROoVLTQAdsYKVv98rweN_bEoSwFwct9DN3Ao/gviz/tq?tqx=out:csv"
df = pd.read_csv(url)
df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], format='%d/%m/%y %H:%M')
df['Radiação'] = df['Radiação'].str.replace(',', '.').astype(float)
df['Temp_Cel'] = df['Temp_Cel'].str.replace(',', '.').astype(float)


# Função para desenhar o gráfico no canvas
def draw_figure(canvas, figure, remove_last_graphics=True):
    # Remove o gráfico anterior se existir
    if remove_last_graphics:
        for widget in canvas.winfo_children():
            widget.destroy()

    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# Função para plotar dados da primeira funcionalidade
def plot_hourly_data(selected_hour, selected_minute, canvas):
    start_time = pd.Timestamp('2019-11-01 00:00:00') + pd.Timedelta(hours=selected_hour)
    end_time = start_time + pd.Timedelta(hours=1)
    filtered_data = df[(df['Data_Hora'] >= start_time) & (df['Data_Hora'] < end_time)]

    if not filtered_data.empty and selected_minute < len(filtered_data):
        temperatura_atual = filtered_data['Temp_Cel'].iloc[selected_minute]
        irradiancia_atual = filtered_data['Radiação'].iloc[selected_minute]

        fig, axs = plt.subplots(1, 2, figsize=(18, 10))

        # Gráfico de Radiação
        axs[0].plot(filtered_data['Data_Hora'], filtered_data['Radiação'], label='Radiação')
        axs[0].scatter(filtered_data['Data_Hora'].iloc[selected_minute], irradiancia_atual, color='red')
        axs[0].annotate(f"{irradiancia_atual:.2f} W/m²",
                        xy=(filtered_data['Data_Hora'].iloc[selected_minute], irradiancia_atual),
                        xytext=(5, 5), textcoords='offset points', fontsize=10, color='red')
        axs[0].set_title('Radiação')
        axs[0].set_xlabel('Data e Hora')
        axs[0].set_ylabel('Radiação (W/m²)')
        axs[0].tick_params(axis='x', rotation=45)

        # Gráfico de Temperatura
        axs[1].plot(filtered_data['Data_Hora'], filtered_data['Temp_Cel'], label='Temperatura')
        axs[1].scatter(filtered_data['Data_Hora'].iloc[selected_minute], temperatura_atual, color='red')
        axs[1].annotate(f"{temperatura_atual:.2f} °C",
                        xy=(filtered_data['Data_Hora'].iloc[selected_minute], temperatura_atual),
                        xytext=(5, 5), textcoords='offset points', fontsize=10, color='red')
        axs[1].set_title('Temperatura')
        axs[1].set_xlabel('Data e Hora')
        axs[1].set_ylabel('Temperatura (°C)')
        axs[1].tick_params(axis='x', rotation=45)

        plt.tight_layout()
        draw_figure(canvas, fig)
        plt.close(fig)


# Funções de cálculo
def deg_to_rad(degrees):
    return degrees * np.pi / 180


def rad_to_deg(radians):
    return radians * 180 / np.pi


def calculate_solar_parameters(data_hora, irradiancia_global, beta, gamma_p, lat, long_local, long_meridiano):
    dia = data_hora.timetuple().tm_yday
    B = (360 / 365) * (dia - 81)
    EoT = 9.87 * np.sin(np.radians(2 * B)) - 7.53 * np.cos(np.radians(B)) - 1.5 * np.sin(np.radians(B))
    EoT /= 60

    hora_local = data_hora.hour + data_hora.minute / 60
    hora_solar = hora_local - ((long_local - long_meridiano) / 15) + EoT

    declinacao_solar = 23.45 * np.sin(np.radians(360 * (284 + dia) / 365))
    omega = 15 * (hora_solar - 12)

    theta_z = np.degrees(np.arccos(np.sin(np.radians(lat)) * np.sin(np.radians(declinacao_solar)) +
                                   np.cos(np.radians(lat)) * np.cos(np.radians(declinacao_solar)) * np.cos(
        np.radians(omega))))

    gamma_solar = np.degrees(np.arctan2(np.sin(np.radians(omega)),
                                        (np.cos(np.radians(omega)) * np.sin(np.radians(lat)) -
                                         np.tan(np.radians(declinacao_solar)) * np.cos(np.radians(lat)))))

    theta_i = np.degrees(
        np.arccos(np.sin(np.radians(theta_z)) * np.cos(np.radians(gamma_p - gamma_solar)) * np.sin(np.radians(beta)) +
                  np.cos(np.radians(theta_z)) * np.cos(np.radians(beta))))

    G_inc = irradiancia_global * np.cos(np.radians(theta_i))
    return hora_solar, theta_i, G_inc


def calcular_resultados(canvas, Pmed, Amp, ang, remove_last_graphics=True):
    # Definindo variáveis
    f = 60
    w = 2 * np.pi * f
    t = np.linspace(0, 2 * (1 / f), 200)

    Vp = Amp * np.sqrt(2)
    Ip = 2 * Pmed / Vp

    # Tensão e corrente
    vt = Vp * np.cos(w * t)
    ph = np.radians(ang)
    it = Ip * np.cos(w * t + ph)

    # Potências
    pt = vt * it
    pt_max = np.max(pt)
    pt_media = np.mean(pt)
    pt_min = np.min(pt)

    # Cálculo da potência reativa
    pa = Vp * Ip / 2 * np.cos(2 * w * t) * np.cos(ph) + Vp * Ip / 2 * np.cos(ph)
    pr = -Vp * Ip / 2 * np.sin(2 * w * t) * np.sin(ph)
    amplitude_tensao = np.max(np.abs(vt))
    amplitude_corrente = np.max(np.abs(it))

    # Potência fotovoltaica
    L = 50e-3
    VL = -np.max(it) * (w * L) * np.sin(w * t)
    Vfv = vt + VL
    pfv = Vfv * (-it)

    pfv_max = np.max(pfv)
    pfv_media = np.mean(pfv)
    pfv_min = np.min(pfv)
    amplitude_tensao_fotovoltaico = np.max(np.abs(Vfv))
    amplitude_corrente_fotovoltaico = np.max(np.abs(-it))

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 5))

    # Figura 1: Tensões e Correntes
    # Subplot 1: Tensões e Correntes com escalas diferentes
    ax1.plot(t * 1e3, vt, 'blue', label='Tensão [V]')
    ax1.set_xlabel('Tempo [ms]')
    ax1.set_ylabel('Tensão [V]', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)

    # Eixo y para a corrente (eixo da direita)
    ax1_corrente = ax1.twinx()
    ax1_corrente.plot(t * 1e3, it, 'orange', label='Corrente [A]')
    ax1_corrente.set_ylabel('Corrente [A]', color='orange')
    ax1_corrente.tick_params(axis='y', labelcolor='orange')

    # Legendas para ambos os eixos
    ax1.legend(loc='upper left')
    ax1_corrente.legend(loc='upper right')

    # Subplot 2: Potências
    ax2.plot(t * 1e3, pa + pr, 'y', label='pa+pr (pt)')
    ax2.plot(t * 1e3, pt, 'k', label='Pt')
    ax2.plot(t * 1e3, pa, 'b', label='P_at')
    ax2.plot(t * 1e3, pr, 'r', label='P_re')
    ax2.grid(True)
    ax2.set_xlabel('Tempo [ms]')
    ax2.set_ylabel('Potência total, ativa e reativa')
    ax2.legend()

    # Figura 3: Potência fotovoltaica
    # Subplot 3: Tensão e corrente fotovoltaica com escalas diferentes
    ax3.plot(t * 1e3, Vfv, 'b', label='Vfv [V]')
    ax3.set_xlabel('Tempo [ms]')
    ax3.set_ylabel('Tensão [V]', color='b')
    ax3.tick_params(axis='y', labelcolor='b')
    ax3.grid(True)

    # Eixo y para a corrente (eixo da direita)
    ax3_corrente = ax3.twinx()
    ax3_corrente.plot(t * 1e3, -it, 'orange', label='Corrente [A]')
    ax3_corrente.set_ylabel('Corrente [A]', color='orange')
    ax3_corrente.tick_params(axis='y', labelcolor='orange')

    # Legendas para ambos os eixos
    ax3.legend(loc='upper left')
    ax3_corrente.legend(loc='upper right')

    # Subplot 4: Potência fotovoltaica
    ax4.plot(t * 1e3, pfv, 'k', label='Pfv')
    ax4.grid(True)
    ax4.set_xlabel('Tempo [ms]')
    ax4.set_ylabel('Potência fotovoltaica [W]')
    ax4.legend()

    plt.tight_layout()
    draw_figure(canvas, fig, remove_last_graphics)  # Desenha a figura no Canvas
    plt.close(fig)

    return (pt_max, pt_media, pt_min, np.mean(pr), Vfv, pfv,
            amplitude_tensao, amplitude_corrente, pfv_max, pfv_min, pfv_media,
            amplitude_tensao_fotovoltaico, amplitude_corrente_fotovoltaico)


def draw_animate(canvas, figure):
    """Embed a Matplotlib figure inside a PySimpleGUI canvas."""
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# Função para criar a placa solar
def create_panel():
    return np.array([[1, -1, 0], [1, 1, 0], [-1, 1, 0], [-1, -1, 0]])


# Função para rotacionar a placa
def rotate_panel(panel, angle_z, angle_x):
    theta_z = np.radians(-angle_z)
    rotation_matrix_z = np.array([
        [np.cos(theta_z), -np.sin(theta_z), 0],
        [np.sin(theta_z), np.cos(theta_z), 0],
        [0, 0, 1]
    ])

    theta_x = np.radians(angle_x)
    rotation_matrix_x = np.array([
        [1, 0, 0],
        [0, np.cos(theta_x), -np.sin(theta_x)],
        [0, np.sin(theta_x), np.cos(theta_x)]
    ])

    rotated_panel = panel @ rotation_matrix_z.T
    rotated_panel = rotated_panel @ rotation_matrix_x.T

    return rotated_panel


# Variável global para a animação
ani = None  # Inicializada como None


def animate(i, angle_x, angle_z, panel, frames, ax, step):
    ax.cla()  # Limpa o gráfico apenas durante a animação

    # Definindo ângulos atuais com base no progresso
    current_angle_x = angle_x * (i / frames)
    current_angle_z = angle_z * (i / frames)

    # Se atingir o último frame, não limpar mais e parar a animação
    if i >= frames:
        current_angle_x = angle_x
        current_angle_z = angle_z
        if ani:  # Parar a animação se `ani` estiver disponível
            ani.event_source.stop()

    # Rotaciona a placa solar
    rotated_panel = rotate_panel(panel, current_angle_z, current_angle_x)

    # Desenhar a placa solar
    if np.all(np.isfinite(rotated_panel)):
        ax.plot_trisurf(rotated_panel[:, 0], rotated_panel[:, 1], rotated_panel[:, 2], color='gray', alpha=0.7)

    # Desenhar vértices e rótulos
    for idx, (x, y, z) in enumerate(rotated_panel):
        ax.scatter(x, y, z, color='black', s=25)
        ax.text(x, y, z, str(idx + 1), color='black', fontsize=12, ha='center')

    # Desenhar os eixos
    ax.quiver(0, 0, 0, 2, 0, 0, color='blue', arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 2, 0, color='green', arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 0, 2, color='red', arrow_length_ratio=0.1)

    # Configurações do gráfico
    ax.set_xlabel('Eixo X')
    ax.set_ylabel('Eixo Y')
    ax.set_zlabel('Eixo Z')
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_zlim(-1, 2)
    ax.set_title(f"Inclinação Z: {current_angle_z:.1f}°, X: {current_angle_x:.1f}°")
    ax.grid(True)


def calcular_geracao_mensal(potencia_sistema, horas_sol_dia, eficiencia):
    return potencia_sistema * horas_sol_dia * eficiencia * 30


def calcular_gasto_sem_painel(consumo_mensal, tarifa):
    return consumo_mensal * tarifa


def calcular_gasto_com_painel(geracao_mensal, consumo_mensal, tarifa):
    return (consumo_mensal - geracao_mensal) * tarifa


def calcular_payback(custo_inicial, economia_mensal):
    if economia_mensal > 0:
        payback = custo_inicial / economia_mensal
        return payback
    else:
        return float('inf')  # Retorna infinito se a economia mensal for 0 ou negativa
