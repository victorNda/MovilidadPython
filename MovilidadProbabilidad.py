"""
=============================================================
  SISTEMA INTELIGENTE DE GESTIÓN DE PARQUEADEROS URBANOS
  Proyecto académico — Python con pandas, numpy, matplotlib
  Basado en: Ramchandani & Benkrid (2026) - DepthPark
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
import os

# ─────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────
TOTAL_ESPACIOS   = 20
TARIFA_POR_MIN   = 150          # COP por minuto
TARIFA_RESERVA   = 2000         # COP costo fijo de reserva
FRANJAS          = ['06-08','08-10','10-12','12-14',
                    '14-16','16-18','18-20','20-22']
OCUP_BASE        = [4, 14, 18, 16, 15, 19, 10, 3]   # vehículos promedio

# DataFrame global de registros
columnas = ['placa','hora_entrada','hora_salida',
            'espacio','tiempo_min','tarifa_cop','estado']
registro_df = pd.DataFrame(columns=columnas)

# Espacios disponibles (True = libre)
espacios = {i: True for i in range(1, TOTAL_ESPACIOS + 1)}

# Reservas activas  {placa: espacio}
reservas = {}


# ═════════════════════════════════════════════
#  MÓDULO 1 — REGISTRO DE ENTRADA Y SALIDA
# ═════════════════════════════════════════════

def espacio_disponible():
    """Retorna el primer espacio libre, o None si no hay."""
    for num, libre in espacios.items():
        if libre:
            return num
    return None


def registrar_entrada(placa: str):
    """Registra el ingreso de un vehículo al parqueadero."""
    global registro_df

    placa = placa.upper().strip()

    # Verificar si ya está adentro
    activos = registro_df[
        (registro_df['placa'] == placa) &
        (registro_df['hora_salida'].isna())
    ]
    if not activos.empty:
        print(f"  [!] La placa {placa} ya se encuentra dentro del parqueadero.")
        return

    # Asignar espacio (reserva prioritaria)
    if placa in reservas:
        num = reservas.pop(placa)
        print(f"  [✓] Reserva encontrada para {placa} → espacio {num}")
    else:
        num = espacio_disponible()

    if num is None:
        print("  [✗] No hay espacios disponibles en este momento.")
        return

    espacios[num] = False
    nueva = {
        'placa':        placa,
        'hora_entrada': datetime.now(),
        'hora_salida':  None,
        'espacio':      num,
        'tiempo_min':   None,
        'tarifa_cop':   None,
        'estado':       'activo'
    }
    registro_df = pd.concat(
        [registro_df, pd.DataFrame([nueva])],
        ignore_index=True
    )
    libres = sum(v for v in espacios.values())
    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║  ENTRADA REGISTRADA              ║")
    print(f"  ║  Placa   : {placa:<22}║")
    print(f"  ║  Espacio : {num:<22}║")
    print(f"  ║  Hora    : {datetime.now().strftime('%H:%M:%S'):<22}║")
    print(f"  ║  Libres  : {libres:<22}║")
    print(f"  ╚══════════════════════════════════╝\n")


def registrar_salida(placa: str):
    """Registra la salida y calcula la tarifa del vehículo."""
    global registro_df

    placa = placa.upper().strip()
    idx = registro_df.index[
        (registro_df['placa'] == placa) &
        (registro_df['hora_salida'].isna())
    ].tolist()

    if not idx:
        print(f"  [✗] Placa {placa} no encontrada o ya salió.")
        return

    i = idx[-1]
    salida  = datetime.now()
    entrada = registro_df.at[i, 'hora_entrada']
    tiempo  = max(1, round((salida - entrada).seconds / 60, 2))
    tarifa  = round(tiempo * TARIFA_POR_MIN)
    num     = registro_df.at[i, 'espacio']

    registro_df.at[i, 'hora_salida'] = salida
    registro_df.at[i, 'tiempo_min']  = tiempo
    registro_df.at[i, 'tarifa_cop']  = tarifa
    registro_df.at[i, 'estado']      = 'finalizado'
    espacios[num] = True

    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║  SALIDA REGISTRADA               ║")
    print(f"  ║  Placa   : {placa:<22}║")
    print(f"  ║  Espacio : {num:<22}║")
    print(f"  ║  Tiempo  : {str(tiempo)+' min':<22}║")
    print(f"  ║  Total   : {'$'+f'{tarifa:,}'+' COP':<22}║")
    print(f"  ╚══════════════════════════════════╝\n")
    return tarifa


# ═════════════════════════════════════════════
#  MÓDULO 2 — RESERVAS
# ═════════════════════════════════════════════

def hacer_reserva(placa: str):
    """Reserva anticipada de un espacio para una placa."""
    placa = placa.upper().strip()

    if placa in reservas:
        print(f"  [!] La placa {placa} ya tiene una reserva activa "
              f"(espacio {reservas[placa]}).")
        return

    num = espacio_disponible()
    if num is None:
        print("  [✗] No hay espacios disponibles para reservar.")
        return

    espacios[num] = False
    reservas[placa] = num
    print(f"\n  [✓] Reserva confirmada")
    print(f"      Placa   : {placa}")
    print(f"      Espacio : {num}")
    print(f"      Costo   : ${TARIFA_RESERVA:,} COP\n")


def cancelar_reserva(placa: str):
    """Cancela una reserva existente."""
    placa = placa.upper().strip()
    if placa in reservas:
        num = reservas.pop(placa)
        espacios[num] = True
        print(f"  [✓] Reserva cancelada para {placa} (espacio {num} liberado).")
    else:
        print(f"  [!] No existe reserva para la placa {placa}.")


def ver_reservas():
    """Muestra todas las reservas activas."""
    if not reservas:
        print("  No hay reservas activas.")
    else:
        print("\n  RESERVAS ACTIVAS:")
        print(f"  {'Placa':<12} {'Espacio':>8}")
        print("  " + "-"*22)
        for p, e in reservas.items():
            print(f"  {p:<12} {e:>8}")
        print()


# ═════════════════════════════════════════════
#  MÓDULO 3 — CONSULTA DE DISPONIBILIDAD
# ═════════════════════════════════════════════

def consultar_disponibilidad():
    """Muestra el estado actual de todos los espacios."""
    libres   = [k for k, v in espacios.items() if v]
    ocupados = [k for k, v in espacios.items() if not v]
    pct      = len(ocupados) / TOTAL_ESPACIOS * 100

    print("\n  ┌─────────────────────────────────────┐")
    print("  │    ESTADO ACTUAL DEL PARQUEADERO    │")
    print("  ├─────────────────────────────────────┤")
    print(f"  │  Total espacios : {TOTAL_ESPACIOS:<19}│")
    print(f"  │  Ocupados       : {len(ocupados):<19}│")
    print(f"  │  Libres         : {len(libres):<19}│")
    print(f"  │  Ocupación      : {pct:.1f}%{'':<16}│")
    print("  ├─────────────────────────────────────┤")

    # Mapa visual de espacios (█ = ocupado, ░ = libre)
    print("  │  MAPA:                              │")
    fila = "  │  "
    for n in range(1, TOTAL_ESPACIOS + 1):
        fila += f"[{'█' if not espacios[n] else '░'}{n:02d}] "
        if n % 5 == 0:
            print(fila + " " * max(0, 38 - len(fila)) + "│")
            fila = "  │  "
    print("  └─────────────────────────────────────┘\n")


# ═════════════════════════════════════════════
#  MÓDULO 4 — ANÁLISIS ESTADÍSTICO (numpy)
# ═════════════════════════════════════════════

def analisis_estadistico():
    """Calcula y muestra estadísticas completas de ocupación."""
    ocup = np.array(OCUP_BASE)
    ocup_pct = (ocup / TOTAL_ESPACIOS) * 100
    prob_disp = (TOTAL_ESPACIOS - ocup) / TOTAL_ESPACIOS

    media     = np.mean(ocup)
    mediana   = np.median(ocup)
    desv_std  = np.std(ocup)
    varianza  = np.var(ocup)
    media_pct = np.mean(ocup_pct)

    # Intervalo de confianza 95%
    ic_inf = max(0, media - 2 * desv_std)
    ic_sup = min(TOTAL_ESPACIOS, media + 2 * desv_std)

    print("\n" + "="*56)
    print("   ANÁLISIS ESTADÍSTICO — SISTEMA DE PARQUEADEROS")
    print("="*56)
    print(f"  Media de ocupación      : {media:.3f} vehículos")
    print(f"  Mediana de ocupación    : {mediana:.1f} vehículos")
    print(f"  Desviación estándar     : {desv_std:.3f} vehículos")
    print(f"  Varianza                : {varianza:.3f}")
    print(f"  Ocupación promedio      : {media_pct:.2f}%")
    print(f"  IC 95% (vehículos)      : [{ic_inf:.2f} — {ic_sup:.2f}]")
    print("-"*56)
    print(f"  {'Franja':<10} {'Veh':>5} {'Ocup%':>7} "
          f"{'P(libre)':>10} {'Estado':>10}")
    print("  " + "-"*50)

    for i, f in enumerate(FRANJAS):
        p = ocup_pct[i]
        estado = ('CRÍTICO' if p >= 85 else
                  'ALTO'    if p >= 65 else
                  'MEDIO'   if p >= 40 else 'BAJO')
        print(f"  {f+'h':<10} {ocup[i]:>5} {p:>6.1f}% "
              f"{prob_disp[i]:>10.2f} {estado:>10}")

    print("="*56 + "\n")
    return ocup_pct, prob_disp


# ═════════════════════════════════════════════
#  MÓDULO 5 — GRÁFICAS (matplotlib)
# ═════════════════════════════════════════════

def generar_graficas():
    """Genera y guarda las gráficas de ocupación y probabilidad."""
    ocup_pct = np.array([20, 70, 90, 80, 75, 95, 50, 15], dtype=float)
    prob_disp = (100 - ocup_pct) / 100
    media_pct = np.mean(ocup_pct)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Sistema de Gestión de Parqueaderos Urbanos\n'
                 'Análisis de Ocupación y Disponibilidad',
                 fontsize=13, fontweight='bold')

    # ── Gráfica 1: barras de ocupación ──
    colores = ['#d32f2f' if p >= 85 else
               '#f57c00' if p >= 65 else
               '#fbc02d' if p >= 40 else
               '#388e3c' for p in ocup_pct]

    bars = axes[0].bar(FRANJAS, ocup_pct, color=colores,
                       edgecolor='white', linewidth=0.8)
    axes[0].axhline(y=media_pct, color='navy', linestyle='--',
                    linewidth=1.8, label=f'Media: {media_pct:.1f}%')
    axes[0].axhline(y=80, color='red', linestyle=':',
                    linewidth=1.2, label='Umbral crítico (80%)')
    axes[0].set_title('Porcentaje de Ocupación por Franja Horaria',
                      fontsize=11)
    axes[0].set_xlabel('Franja horaria')
    axes[0].set_ylabel('Ocupación (%)')
    axes[0].set_ylim(0, 115)
    axes[0].legend(fontsize=9)
    axes[0].tick_params(axis='x', rotation=30)
    for bar, v in zip(bars, ocup_pct):
        axes[0].text(bar.get_x() + bar.get_width()/2,
                     v + 1.5, f'{v:.0f}%',
                     ha='center', va='bottom', fontsize=9)

    # ── Gráfica 2: línea de probabilidad ──
    x = range(len(FRANJAS))
    axes[1].plot(x, prob_disp, marker='o', color='#1565c0',
                 linewidth=2.5, markersize=8, zorder=3)
    axes[1].fill_between(x, prob_disp, alpha=0.12, color='#1565c0')
    axes[1].axhline(y=0.5, color='orange', linestyle='--',
                    linewidth=1.2, label='50% probabilidad')
    axes[1].set_title('Probabilidad de Espacio Disponible',
                      fontsize=11)
    axes[1].set_xlabel('Franja horaria')
    axes[1].set_ylabel('Probabilidad P(disponible)')
    axes[1].set_ylim(-0.05, 1.10)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(FRANJAS, rotation=30)
    axes[1].legend(fontsize=9)
    for xi, v in zip(x, prob_disp):
        axes[1].annotate(f'{v:.0%}', (xi, v),
                         textcoords='offset points',
                         xytext=(0, 10), ha='center', fontsize=9)

    # Leyenda de colores
    from matplotlib.patches import Patch
    leyenda = [Patch(color='#d32f2f', label='Crítico ≥85%'),
               Patch(color='#f57c00', label='Alto 65-84%'),
               Patch(color='#fbc02d', label='Medio 40-64%'),
               Patch(color='#388e3c', label='Bajo <40%')]
    axes[0].legend(handles=leyenda +
                   [plt.Line2D([0],[0], color='navy',
                               linestyle='--', label=f'Media: {media_pct:.1f}%'),
                    plt.Line2D([0],[0], color='red',
                               linestyle=':', label='Umbral 80%')],
                   fontsize=8, loc='upper left')

    plt.tight_layout()
    plt.savefig('grafica_ocupacion.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("  [✓] Gráfica guardada: grafica_ocupacion.png\n")


def grafica_simulacion():
    """Genera la gráfica de simulación hora a hora."""
    np.random.seed(42)
    horas = list(range(6, 23))
    ocup_sim = []

    for hora in horas:
        bloque = min((hora - 6) // 2, len(OCUP_BASE) - 1)
        base = OCUP_BASE[bloque]
        variacion = np.random.randint(
            -max(1, int(base * 0.2)),
             max(1, int(base * 0.2)) + 1
        )
        ocup_sim.append(max(0, min(TOTAL_ESPACIOS, base + variacion)))

    # Salida en consola
    print("\n  SIMULACIÓN DE OCUPACIÓN HORA A HORA")
    print("  " + "-"*48)
    for h, v in zip(horas, ocup_sim):
        estado = ("LLENO"   if v == TOTAL_ESPACIOS else
                  "CRÍTICO" if v >= 18 else
                  "ALTO"    if v >= 14 else
                  "NORMAL")
        barra = "█" * v + "░" * (TOTAL_ESPACIOS - v)
        print(f"  {h:02d}:00 | {barra} | {v:2d}/{TOTAL_ESPACIOS} | {estado}")

    # Gráfica
    plt.figure(figsize=(13, 5))
    plt.step(horas, ocup_sim, where='mid', color='#1565c0',
             linewidth=2.5, label='Ocupación simulada')
    plt.fill_between(horas, ocup_sim, step='mid',
                     alpha=0.10, color='#1565c0')
    plt.axhline(y=TOTAL_ESPACIOS * 0.8, color='orange',
                linestyle='--', linewidth=1.5,
                label='Umbral crítico (80%)')
    plt.axhline(y=TOTAL_ESPACIOS, color='red',
                linewidth=1.0, linestyle='-',
                label='Capacidad máxima')

    plt.title('Simulación de Ocupación por Hora — Parqueadero Urbano',
              fontsize=13, fontweight='bold')
    plt.xlabel('Hora del día')
    plt.ylabel('Número de vehículos')
    plt.xticks(horas, [f'{h:02d}:00' for h in horas], rotation=45)
    plt.yticks(range(0, TOTAL_ESPACIOS + 2, 2))
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('simulacion_ocupacion.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("  [✓] Gráfica guardada: simulacion_ocupacion.png\n")


def grafica_distribucion():
    """Gráfica de pastel: distribución por nivel de demanda."""
    categorias = ['Alta (≥80%)', 'Media (50-79%)', 'Baja (<50%)']
    valores    = [2, 4, 2]       # número de franjas por categoría
    colores    = ['#d32f2f', '#f57c00', '#388e3c']
    explode    = (0.05, 0.02, 0.02)

    plt.figure(figsize=(7, 6))
    wedges, texts, autotexts = plt.pie(
        valores, labels=categorias, colors=colores,
        explode=explode, autopct='%1.0f%%',
        startangle=140, textprops={'fontsize': 11}
    )
    for at in autotexts:
        at.set_fontweight('bold')

    plt.title('Distribución de Franjas Horarias\npor Nivel de Demanda',
              fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('distribucion_demanda.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("  [✓] Gráfica guardada: distribucion_demanda.png\n")


# ═════════════════════════════════════════════
#  MÓDULO 6 — REPORTE AUTOMÁTICO
# ═════════════════════════════════════════════

def generar_reporte():
    """Genera y guarda un reporte estadístico completo en .txt"""
    ocup     = np.array(OCUP_BASE)
    ocup_pct = (ocup / TOTAL_ESPACIOS) * 100
    prob     = (TOTAL_ESPACIOS - ocup) / TOTAL_ESPACIOS

    media    = np.mean(ocup_pct)
    maxima   = np.max(ocup_pct)
    minima   = np.min(ocup_pct)
    std      = np.std(ocup_pct)
    pico     = FRANJAS[int(np.argmax(ocup_pct))]

    # Resumen del registro real (si hay datos)
    total_vehiculos = len(registro_df)
    ingresos_totales = (registro_df['tarifa_cop'].dropna().sum()
                        if not registro_df.empty else 0)

    reporte = f"""
{'='*58}
   REPORTE ESTADÍSTICO — SISTEMA DE PARQUEADEROS URBANOS
   Fecha de generación : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
   Total de espacios   : {TOTAL_ESPACIOS}
{'='*58}

INDICADORES GENERALES
  Ocupación promedio diaria  : {media:.2f}%
  Ocupación máxima           : {maxima:.0f}% (franja {pico}h)
  Ocupación mínima           : {minima:.0f}%
  Desviación estándar        : {std:.2f}%
  Intervalo de confianza 95% : [{max(0, media-2*std):.1f}% — {min(100, media+2*std):.1f}%]

ESTADÍSTICAS DE USO (sesión actual)
  Vehículos registrados      : {total_vehiculos}
  Ingresos generados         : ${ingresos_totales:,.0f} COP
  Espacios actualmente libres: {sum(v for v in espacios.values())}

ANÁLISIS POR FRANJA HORARIA
{'Franja':<12}{'Veh':>5}{'Ocup%':>8}{'P(libre)':>10}{'Estado':>12}
{'-'*50}"""

    for i, f in enumerate(FRANJAS):
        p = ocup_pct[i]
        estado = ('CRÍTICO' if p >= 85 else
                  'ALTO'    if p >= 65 else
                  'MEDIO'   if p >= 40 else 'BAJO')
        reporte += (f"\n{f+'h':<12}{int(ocup[i]):>5}"
                    f"{p:>7.1f}%{prob[i]:>10.2f}{estado:>12}")

    reporte += f"""

CLASIFICACIÓN POR NIVEL DE DEMANDA
  Alta  (≥80%) : franjas 10-12h y 16-18h  →  25% del día
  Media (50-79%): franjas 08-10h, 12-14h,
                  14-16h, 18-20h           →  50% del día
  Baja  (<50%) : franjas 06-08h y 20-22h  →  25% del día

CONCLUSIONES DEL REPORTE
  • Hora pico         : {pico}h con {maxima:.0f}% de ocupación
  • P(disponible) min : {prob[int(np.argmax(ocup_pct))]:.0%} en hora pico
  • P(disponible) max : {prob[int(np.argmin(ocup_pct))]:.0%} en hora valle
  • Se recomienda implementar tarifas dinámicas en horas pico
    y descuentos en las franjas de baja demanda.

{'='*58}
  Generado por: Sistema de Parqueaderos — Python
  Librerías : pandas {pd.__version__} | numpy {np.__version__}
{'='*58}
"""

    nombre = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(nombre, 'w', encoding='utf-8') as f:
        f.write(reporte)

    print(reporte)
    print(f"  [✓] Reporte guardado: {nombre}\n")


# ═════════════════════════════════════════════
#  MÓDULO 7 — MENÚ PRINCIPAL
# ═════════════════════════════════════════════

def menu():
    """Menú interactivo del sistema."""
    print("\n" + "█"*50)
    print("  SISTEMA DE GESTIÓN DE PARQUEADEROS URBANOS")
    print("  Basado en: Ramchandani & Benkrid (2026)")
    print("█"*50)

    opciones = {
        '1': ('Registrar entrada de vehículo',      _op_entrada),
        '2': ('Registrar salida de vehículo',        _op_salida),
        '3': ('Consultar disponibilidad',            consultar_disponibilidad),
        '4': ('Hacer reserva',                       _op_reserva),
        '5': ('Cancelar reserva',                    _op_cancelar_reserva),
        '6': ('Ver reservas activas',                ver_reservas),
        '7': ('Análisis estadístico',                analisis_estadistico),
        '8': ('Generar gráfica de ocupación',        generar_graficas),
        '9': ('Generar simulación hora a hora',      grafica_simulacion),
        '10':('Generar gráfica de distribución',     grafica_distribucion),
        '11':('Generar reporte automático (.txt)',    generar_reporte),
        '12':('Ver todos los registros',             _op_ver_registros),
        '0': ('Salir',                               None),
    }

    while True:
        print("\n  ─── MENÚ ───────────────────────────────")
        for k, (desc, _) in opciones.items():
            print(f"   [{k:>2}] {desc}")
        print("  ────────────────────────────────────────")
        op = input("  Seleccione una opción: ").strip()

        if op == '0':
            print("\n  Sistema cerrado. ¡Hasta pronto!\n")
            break
        elif op in opciones:
            _, fn = opciones[op]
            fn()
        else:
            print("  [!] Opción no válida. Intente de nuevo.")


# ─── Funciones auxiliares de menú ─────────────

def _op_entrada():
    placa = input("  Ingrese la placa del vehículo: ").strip()
    if placa:
        registrar_entrada(placa)

def _op_salida():
    placa = input("  Ingrese la placa del vehículo: ").strip()
    if placa:
        registrar_salida(placa)

def _op_reserva():
    placa = input("  Ingrese la placa a reservar: ").strip()
    if placa:
        hacer_reserva(placa)

def _op_cancelar_reserva():
    placa = input("  Ingrese la placa de la reserva a cancelar: ").strip()
    if placa:
        cancelar_reserva(placa)

def _op_ver_registros():
    if registro_df.empty:
        print("\n  No hay registros en esta sesión.")
    else:
        print("\n  REGISTROS DE LA SESIÓN:")
        print(registro_df[['placa','espacio','hora_entrada',
                            'tiempo_min','tarifa_cop','estado']]
              .to_string(index=False))
        print()


# ═════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ═════════════════════════════════════════════

if __name__ == '__main__':
    # Demo rápida (opcional): comenta este bloque para ir directo al menú
    print("\n  Ejecutando demo rápida del sistema...")
    registrar_entrada("ABC123")
    registrar_entrada("XYZ789")
    hacer_reserva("DEF456")
    consultar_disponibilidad()
    registrar_salida("ABC123")
    analisis_estadistico()
    generar_reporte()
    print("\n  Demo completada. Iniciando menú interactivo...")
    input("  Presione ENTER para continuar...")

    # Menú interactivo
    menu()