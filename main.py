# ============================================================================
# MÓDULO: main.py
# Descripción: Punto de entrada principal del sistema. Ejecuta pruebas de
#              verificación en consola y lanza la interfaz gráfica Tkinter.
# ============================================================================
import tkinter as tk
from modelo import RegistroDuplicadoError
from patrones import GestorBaseDatos, FabricaPersonas
from servicios_funcionales import (
    filtrar_urgencias_adultos_mayores,
    generar_reporte_anonimizado,
    calcular_total_urgencias
)
from interfaz_eventos import AplicacionSistemaRural


def ejecutar_pruebas_y_precarga() -> None:
    """Precarga datos ficticios e imprime las verificaciones en consola."""
    db = GestorBaseDatos()
    print(f"Singleton GestorBaseDatos activo: {GestorBaseDatos() is db}")

    registros_ficticios = [
        {
            "dni": "00000001", "nombre": "Ana Lucía Torres", "telefono": "900000001",
            "edad": 68, "comunidad": "Caserío El Tambo", "urgente": True
        },
        {
            "dni": "00000002", "nombre": "Pedro Huamán Díaz", "telefono": "900000002",
            "edad": 35, "comunidad": "Chugur Centro", "urgente": False
        },
        {
            "dni": "00000003", "nombre": "Rosaura Chilón Vega", "telefono": "900000003",
            "edad": 74, "comunidad": "Caserío Perlamayo", "urgente": True
        }
    ]

    for datos in registros_ficticios:
        paciente = FabricaPersonas.crear_persona("PACIENTE", datos)
        db.registrar_paciente(paciente)

    pacientes = db.listar_pacientes()
    mayores_urg = filtrar_urgencias_adultos_mayores(pacientes)

    print(f"Pacientes registrados (ficticios): {len(pacientes)}")
    print(f"Total atenciones urgentes (reduce): {calcular_total_urgencias(pacientes)}")
    print(f"Urgencias adultos mayores >=60 (filter): {len(mayores_urg)}")

    print("Salida map() anonimizada (Ley 29733):")
    for linea in generar_reporte_anonimizado(mayores_urg):
        print(f" -> {linea}")

    print("Prueba duplicado DNI '00000001':")
    try:
        duplicado = FabricaPersonas.crear_persona("PACIENTE", registros_ficticios[0])
        db.registrar_paciente(duplicado)
    except RegistroDuplicadoError:
        print(" -> RegistroDuplicadoError capturado OK")


if __name__ == "__main__":
    ejecutar_pruebas_y_precarga()
    ventana_principal = tk.Tk()
    app = AplicacionSistemaRural(ventana_principal)
    ventana_principal.mainloop()
