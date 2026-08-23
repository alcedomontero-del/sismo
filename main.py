"""
=============================================================================
ALARMA ANTISÍSMICA PARA ANDROID (KIVY + PLYER)
=============================================================================
Aplicación móvil en Python para detección sísmica mediante acelerómetro.
- Monitoreo en tiempo real de aceleración (X, Y, Z).
- Calibración automática de gravedad en reposo.
- Sismógrafo gráfico en tiempo real.
- Sirena acústica de alta potencia y vibración háptica.
- Modo simulación para pruebas en PC / emulador.
=============================================================================
"""

import os
import math
import collections
from siren_generator import generar_sirena_wav

# Inicializar Kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.utils import platform

# Soporte de sensores Android mediante Plyer
ACCEL_DISPONIBLE = False
VIBRATOR_DISPONIBLE = False

try:
    from plyer import accelerometer
    try:
        accelerometer.enable()
        ACCEL_DISPONIBLE = True
    except Exception:
        ACCEL_DISPONIBLE = False
except Exception:
    ACCEL_DISPONIBLE = False

try:
    from plyer import vibrator
    VIBRATOR_DISPONIBLE = True
except Exception:
    VIBRATOR_DISPONIBLE = False


class SismografoWidget(Widget):
    """Lienzo gráfico que dibuja las ondas sísmicas en tiempo real."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.puntos_onda = collections.deque(maxlen=60)
        for _ in range(60):
            self.puntos_onda.append(0.0)
        self.bind(pos=self.actualizar_grafico, size=self.actualizar_grafico)

    def agregar_lectura(self, valor_vibracion):
        self.puntos_onda.append(valor_vibracion)
        self.actualizar_grafico()

    def actualizar_grafico(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Fondo del sismógrafo
            Color(0.08, 0.09, 0.11, 1.0)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

            # Líneas guía de cuadrícula
            Color(0.18, 0.22, 0.28, 0.6)
            mid_y = self.y + self.height / 2
            Line(points=[self.x, mid_y, self.x + self.width, mid_y], width=1)
            Line(points=[self.x, self.y + self.height * 0.75, self.x + self.width, self.y + self.height * 0.75], width=0.8, dash_length=4)
            Line(points=[self.x, self.y + self.height * 0.25, self.x + self.width, self.y + self.height * 0.25], width=0.8, dash_length=4)

            # Dibujo de la onda sísmica
            if len(self.puntos_onda) > 1:
                Color(0.0, 0.9, 0.8, 1.0)
                step_x = self.width / (len(self.puntos_onda) - 1)
                line_points = []
                for i, v in enumerate(self.puntos_onda):
                    px = self.x + i * step_x
                    # Escalar vibración a la altura del widget
                    desp_y = (v * (self.height * 0.4))
                    desp_y = max(-self.height * 0.45, min(self.height * 0.45, desp_y))
                    py = mid_y + desp_y
                    line_points.extend([px, py])
                Line(points=line_points, width=1.6)


class AlarmaSismicaApp(App):
    def build(self):
        self.title = "Alerta Sísmica Android"
        
        # Tamaño de ventana para pruebas en PC
        if platform not in ('android', 'ios'):
            Window.size = (380, 680)

        # Estados de la aplicación: 'DESARMADO', 'CALIBRANDO', 'ARMADO', 'ALARMA'
        self.estado = 'DESARMADO'
        self.gravedad_base = 9.81
        self.muestras_calibracion = []
        self.tiempo_calibracion = 5
        self.sensibilidad_umbral = 0.35  # m/s^2 sobre la base
        self.historial_reciente = collections.deque(maxlen=8)
        self.simulando_sismo = False
        self.sim_frame = 0

        # Generar o cargar sirena
        sirena_path = generar_sirena_wav("sirena.wav")
        self.sonido_alarma = SoundLoader.load(sirena_path)
        if self.sonido_alarma:
            self.sonido_alarma.loop = True
            self.sonido_alarma.volume = 1.0

        # Layout Principal
        self.root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        self.dibujar_fondo_principal()

        # 1. Cabecera / Título
        lbl_titulo = Label(
            text="[b]ALARMA SÍSMICA[/b]\n[size=13]Detector Acelerométrico de Sismos[/size]",
            markup=True,
            size_hint_y=None,
            height=60,
            halign='center',
            color=(1, 1, 1, 1)
        )
        self.root.add_widget(lbl_titulo)

        # 2. Indicador de Estado (Badge)
        self.lbl_estado = Label(
            text="[b]DESARMADO[/b]",
            markup=True,
            size_hint_y=None,
            height=45,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.root.add_widget(self.lbl_estado)

        # 3. Sismógrafo en tiempo real
        self.sismografo = SismografoWidget(size_hint_y=0.25)
        self.root.add_widget(self.sismografo)

        # 4. Lecturas de Aceleración y Nivel de Vibración
        self.lbl_lecturas = Label(
            text="X: 0.00  |  Y: 0.00  |  Z: 0.00\nVibración: 0.000 m/s²",
            size_hint_y=None,
            height=45,
            font_size='13sp',
            color=(0.85, 0.88, 0.92, 1)
        )
        self.root.add_widget(self.lbl_lecturas)

        # 5. Panel de Sensibilidad
        grid_sens = GridLayout(cols=3, size_hint_y=None, height=40, spacing=6)
        self.btn_sens_alta = Button(text="Alta (0.15)", background_color=(0.2, 0.4, 0.6, 1))
        self.btn_sens_media = Button(text="Media (0.35)", background_color=(0.2, 0.6, 0.4, 1))
        self.btn_sens_baja = Button(text="Baja (0.70)", background_color=(0.4, 0.4, 0.4, 1))

        self.btn_sens_alta.bind(on_release=lambda x: self.fijar_sensibilidad(0.15, self.btn_sens_alta))
        self.btn_sens_media.bind(on_release=lambda x: self.fijar_sensibilidad(0.35, self.btn_sens_media))
        self.btn_sens_baja.bind(on_release=lambda x: self.fijar_sensibilidad(0.70, self.btn_sens_baja))

        grid_sens.add_widget(self.btn_sens_alta)
        grid_sens.add_widget(self.btn_sens_media)
        grid_sens.add_widget(self.btn_sens_baja)
        self.root.add_widget(grid_sens)

        # Slider para ajuste fino
        box_slider = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        box_slider.add_widget(Label(text="Umbral:", size_hint_x=0.25, font_size='12sp'))
        self.slider_sens = Slider(min=0.05, max=1.50, value=0.35, step=0.05, size_hint_x=0.55)
        self.slider_sens.bind(value=self.on_slider_change)
        self.lbl_slider_val = Label(text="0.35 m/s²", size_hint_x=0.20, font_size='12sp')
        box_slider.add_widget(self.slider_sens)
        box_slider.add_widget(self.lbl_slider_val)
        self.root.add_widget(box_slider)

        # 6. Botones de Acción Principal
        self.btn_armar = Button(
            text="[b]CALIBRAR Y ARMAR ALARMA[/b]",
            markup=True,
            size_hint_y=None,
            height=50,
            background_color=(0.15, 0.75, 0.35, 1)
        )
        self.btn_armar.bind(on_release=self.toggle_armado)
        self.root.add_widget(self.btn_armar)

        # Botón de simulación (ideal para pruebas en PC)
        self.btn_simular = Button(
            text="🧪 Simular Sismo (Prueba)",
            size_hint_y=None,
            height=40,
            background_color=(0.3, 0.3, 0.35, 1)
        )
        self.btn_simular.bind(on_release=self.toggle_simulacion)
        self.root.add_widget(self.btn_simular)

        # 7. Panel de Instrucción / Emergencia
        self.lbl_info = Label(
            text="Coloca el móvil sobre una mesa firme y presiona 'Calibrar y Armar'.",
            size_hint_y=None,
            height=50,
            font_size='12sp',
            color=(0.7, 0.75, 0.8, 1),
            halign='center'
        )
        self.root.add_widget(self.lbl_info)

        # Iniciar bucle de muestreo de sensor (30 Hz)
        Clock.schedule_interval(self.procesar_lectura_sensor, 1.0 / 30.0)
        self.fijar_sensibilidad(0.35, self.btn_sens_media)

        return self.root

    def dibujar_fondo_principal(self):
        with self.root.canvas.before:
            Color(0.05, 0.06, 0.08, 1.0)
            self.rect_fondo = Rectangle(pos=self.root.pos, size=self.root.size)
        self.root.bind(pos=self._actualizar_fondo, size=self._actualizar_fondo)

    def _actualizar_fondo(self, *args):
        self.rect_fondo.pos = self.root.pos
        self.rect_fondo.size = self.root.size

    def fijar_sensibilidad(self, valor, btn_activo=None):
        self.sensibilidad_umbral = valor
        self.slider_sens.value = valor
        self.lbl_slider_val.text = f"{valor:.2f} m/s²"

    def on_slider_change(self, instance, value):
        self.sensibilidad_umbral = round(value, 2)
        self.lbl_slider_val.text = f"{self.sensibilidad_umbral:.2f} m/s²"

    def toggle_armado(self, *args):
        if self.estado == 'DESARMADO':
            self.iniciar_calibracion()
        elif self.estado in ('ARMADO', 'CALIBRANDO', 'ALARMA'):
            self.desarmar_alarma()

    def iniciar_calibracion(self):
        self.estado = 'CALIBRANDO'
        self.muestras_calibracion.clear()
        self.cuenta_regresiva = 5
        self.lbl_estado.text = "[b][color=ffcc00]CALIBRANDO... SUELTA EL MÓVIL[/color][/b]"
        self.btn_armar.text = "[b]CANCELAR[/b]"
        self.btn_armar.background_color = (0.7, 0.2, 0.2, 1)
        self.lbl_info.text = f"Calibrando superficie en {self.cuenta_regresiva}s...\nNo toques el dispositivo."
        Clock.schedule_interval(self._paso_cuenta_regresiva, 1.0)

    def _paso_cuenta_regresiva(self, dt):
        self.cuenta_regresiva -= 1
        if self.cuenta_regresiva > 0:
            self.lbl_info.text = f"Calibrando superficie en {self.cuenta_regresiva}s...\nNo toques el dispositivo."
        else:
            Clock.unschedule(self._paso_cuenta_regresiva)
            self.finalizar_calibracion()

    def finalizar_calibracion(self):
        if self.muestras_calibracion:
            self.gravedad_base = sum(self.muestras_calibracion) / len(self.muestras_calibracion)
        else:
            self.gravedad_base = 9.81

        self.estado = 'ARMADO'
        self.lbl_estado.text = "[b][color=00ff88]● VIGILANCIA ACTIVA (ARMADO)[/color][/b]"
        self.btn_armar.text = "[b]DESACTIVAR ALARMA[/b]"
        self.btn_armar.background_color = (0.8, 0.25, 0.2, 1)
        self.lbl_info.text = "Sistema armado. Ante cualquier vibración anómala\nse activará la sirena de emergencia."

    def desarmar_alarma(self):
        self.estado = 'DESARMADO'
        self.simulando_sismo = False
        self.detener_alerta_acustica()
        self.lbl_estado.text = "[b][color=aaaaaa]DESARMADO[/color][/b]"
        self.btn_armar.text = "[b]CALIBRAR Y ARMAR ALARMA[/b]"
        self.btn_armar.background_color = (0.15, 0.75, 0.35, 1)
        self.lbl_info.text = "Coloca el móvil sobre una mesa firme y presiona 'Calibrar y Armar'."

    def disparar_alarma(self):
        if self.estado == 'ALARMA':
            return
        self.estado = 'ALARMA'
        self.lbl_estado.text = "[b][color=ff2222]¡¡¡ ALERTA SÍSMICA DETECTADA !!![/color][/b]"
        self.lbl_info.text = "[b]¡AGÁCHATE, CÚBRETE Y SUJÉTATE!\nALÉJATE DE VENTANAS Y OBJETOS PESADOS.[/b]"
        self.btn_armar.text = "[b]SILENCIAR Y APAGAR[/b]"
        self.btn_armar.background_color = (1.0, 0.1, 0.1, 1)

        # Reproducir sirena
        if self.sonido_alarma and self.sonido_alarma.state != 'play':
            self.sonido_alarma.play()

        # Vibración en Android
        if VIBRATOR_DISPONIBLE:
            try:
                vibrator.vibrate(3)
            except Exception:
                pass

        # Efecto estroboscópico de pantalla
        Clock.schedule_interval(self._efecto_estroboscopico, 0.25)

    def _efecto_estroboscopico(self, dt):
        if self.estado != 'ALARMA':
            Clock.unschedule(self._efecto_estroboscopico)
            self._actualizar_fondo()
            return
        # Alternar color de fondo rojo / oscuro
        self.canvas.before.clear()
        with self.root.canvas.before:
            if hasattr(self, '_flash_toggle') and self._flash_toggle:
                Color(0.8, 0.05, 0.05, 1.0)
                self._flash_toggle = False
            else:
                Color(0.1, 0.02, 0.02, 1.0)
                self._flash_toggle = True
            self.rect_fondo = Rectangle(pos=self.root.pos, size=self.root.size)

    def detener_alerta_acustica(self):
        if self.sonido_alarma:
            self.sonido_alarma.stop()
        Clock.unschedule(self._efecto_estroboscopico)
        self._actualizar_fondo()

    def toggle_simulacion(self, *args):
        self.simulando_sismo = not self.simulando_sismo
        if self.simulando_sismo:
            self.btn_simular.text = "Detener Simulación"
            self.btn_simular.background_color = (0.8, 0.3, 0.1, 1)
        else:
            self.btn_simular.text = "🧪 Simular Sismo (Prueba)"
            self.btn_simular.background_color = (0.3, 0.3, 0.35, 1)

    def procesar_lectura_sensor(self, dt):
        # 1. Obtener valores x, y, z
        x, y, z = 0.0, 0.0, 9.81
        if ACCEL_DISPONIBLE:
            try:
                val = accelerometer.acceleration
                if val and val[0] is not None:
                    x, y, z = val[0], val[1], val[2]
            except Exception:
                pass

        # Si estamos en modo de simulación de sismo
        if self.simulando_sismo:
            self.sim_frame += 1
            ruido_sismo = (math.sin(self.sim_frame * 0.8) + math.cos(self.sim_frame * 1.3)) * 1.5
            x += ruido_sismo
            y += ruido_sismo * 0.5
            z += ruido_sismo * 0.8

        # 2. Magnitud total del vector de aceleración
        mag_total = math.sqrt(x**2 + y**2 + z**2)

        if self.estado == 'CALIBRANDO':
            self.muestras_calibracion.append(mag_total)

        # 3. Calcular vibración relativa respecto al reposo
        vibracion_actual = abs(mag_total - self.gravedad_base)
        self.historial_reciente.append(vibracion_actual)
        vibracion_filtrada = sum(self.historial_reciente) / len(self.historial_reciente)

        # 4. Actualizar interfaz y gráfico
        self.sismografo.agregar_lectura(vibracion_filtrada)
        self.lbl_lecturas.text = f"X: {x:+.2f}  |  Y: {y:+.2f}  |  Z: {z:+.2f}\nVibración: {vibracion_filtrada:.3f} m/s² (Umbral: {self.sensibilidad_umbral:.2f})"

        # 5. Lógica de activación de alarma
        if self.estado == 'ARMADO':
            if vibracion_filtrada >= self.sensibilidad_umbral:
                self.disparar_alarma()


if __name__ == '__main__':
    AlarmaSismicaApp().run()
