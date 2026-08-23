# 🌋 Alarma Antisísmica para Android (Python -> APK)

Esta aplicación móvil desarrollada en **Python (Kivy + Plyer)** transforma tu teléfono Android en un detector sísmico de alta precisión utilizando el acelerómetro interno del móvil.

---

## ✨ Características Principales

1. **Detección Sísmica por Acelerómetro**:
   - Monitorea continuamente las fuerzas en los 3 ejes ($X, Y, Z$) y el vector de aceleración total.
   - Algoritmo de filtrado de ruido y desviación estándar para detectar ondas sísmicas $P$ y $S$.

2. **Calibración Automática de Reposo**:
   - Cuenta regresiva de 5 segundos para colocar el teléfono sobre una mesa o superficie plana.
   - Auto-calibra la gravedad local ($\approx 9.81\text{ m/s}^2$) para evitar falsas alarmas.

3. **Sismógrafo en Tiempo Real**:
   - Muestra visualmente las oscilaciones y microvibraciones en pantalla como un sismógrafo profesional.

4. **Respuesta de Emergencia**:
   - **Sirena acústica de alta potencia** (`sirena.wav`).
   - **Vibración háptica continua** en Android (`plyer.vibrator`).
   - **Pantalla estroboscópica de alerta roja** con recomendaciones de evacuación (*"Agáchate, Cúbrete, Sujétate"*).
   - Botón de silencio y rearme.

5. **Ajuste de Sensibilidad**:
   - Alta ($0.15\text{ m/s}^2$), Media ($0.35\text{ m/s}^2$), Baja ($0.70\text{ m/s}^2$) y control deslizante manual.

6. **Modo Simulación**:
   - Permite probar la alarma y la sirena directamente en PC / emulador con el botón `🧪 Simular Sismo`.

---

## 🚀 Cómo probar en PC (Windows)

1. Instala las dependencias:
   ```bash
   pip install kivy plyer
   ```
2. Ejecuta la aplicación:
   ```bash
   python main.py
   ```

---

## 📱 Cómo generar el APK (3 Opciones Fáciles)

### Opción 1: Google Colab (100% Gratis en la Nube - Recomendada)
1. Entra a [Google Colab](https://colab.research.google.com/).
2. Haz clic en **Subir (Upload)** y sube el archivo [`compilar_apk_colab.ipynb`](file:///c:/Users/Tecnomaster/Downloads/anti/compilar_apk_colab.ipynb).
3. Sube los archivos del proyecto (`main.py`, `siren_generator.py`, `buildozer.spec`).
4. Ejecuta las celdas del cuaderno en orden. En ~5 minutos descargará automáticamente el archivo `.apk` a tu equipo.

---

### Opción 2: GitHub Actions (Automático al subir a GitHub)
1. Sube tu código a un repositorio en GitHub.
2. El archivo de flujo ya incluido en `.github/workflows/build_apk.yml` compilará el APK automáticamente en cada commit.
3. Ve a la pestaña **Actions** en tu GitHub y descarga el artefacto `Alarma-Sismica-APK`.

---

### Opción 3: Compilar Localmente con WSL (Linux en Windows)
Si tienes WSL / Ubuntu instalado en Windows:
```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip install --upgrade pip
pip install Cython==0.29.36 buildozer virtualenv
buildozer -v android debug
```
El archivo `.apk` resultante se guardará en la carpeta `bin/`.
