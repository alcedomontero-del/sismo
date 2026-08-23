"""
Generador de sonido de sirena de emergencia en formato WAV puro (sin dependencias externas).
Crea un archivo 'sirena.wav' con un tono de alerta modulado en frecuencia.
"""

import wave
import struct
import math
import os

def generar_sirena_wav(archivo_salida="sirena.wav", duracion_seg=3.0, sample_rate=44100):
    """Genera un archivo WAV con sonido de sirena oscilante (wail/yelp)."""
    if os.path.exists(archivo_salida) and os.path.getsize(archivo_salida) > 1000:
        return archivo_salida

    num_samples = int(duracion_seg * sample_rate)
    f_min = 600.0   # Frecuencia mínima en Hz
    f_max = 1200.0  # Frecuencia máxima en Hz
    mod_freq = 2.0  # Ciclos de modulación por segundo (sube y baja 2 veces por seg)

    datos_audio = bytearray()

    fase = 0.0
    for i in range(num_samples):
        t = i / sample_rate
        # Frecuencia instantánea oscilante (onda senoidal entre f_min y f_max)
        f_inst = f_min + (f_max - f_min) * (0.5 * (1 + math.sin(2 * math.pi * mod_freq * t)))
        fase += 2 * math.pi * f_inst / sample_rate
        
        # Onda principal (con armónico para mayor agresividad sonora)
        muestra = 0.7 * math.sin(fase) + 0.3 * math.sin(2 * fase)
        
        # Escalar a 16-bit PCM con volumen alto
        val_int = int(muestra * 30000)
        val_int = max(-32767, min(32767, val_int))
        
        datos_audio.extend(struct.pack('<h', val_int))

    with wave.open(archivo_salida, 'w') as wav_file:
        wav_file.setnchannels(1)       # Mono
        wav_file.setsampwidth(2)      # 16 bits
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(datos_audio)

    return archivo_salida

if __name__ == "__main__":
    archivo = generar_sirena_wav()
    print(f"Archivo de sirena generado exitosamente: {archivo}")
