# ============================================================================
# MÓDULO: servicios_funcionales.py
# Descripción: Consultas y reportes estadísticos mediante funciones puras
#              de orden superior (filter, map, reduce) sin efectos secundarios.
# ============================================================================
from functools import reduce
from modelo import Paciente


def filtrar_urgencias_adultos_mayores(pacientes: list[Paciente]) -> list[Paciente]:
    """Filtra pacientes con atención urgente y edad >= 60 años sin mutar la colección."""
    return list(filter(lambda p: p.es_urgente() and p.get_edad() >= 60, pacientes))


def generar_reporte_anonimizado(pacientes: list[Paciente]) -> list[str]:
    """Transforma objetos Paciente en cadenas de texto protegidas mediante map()."""
    return list(map(lambda p: p.obtener_resumen(), pacientes))


def calcular_total_urgencias(pacientes: list[Paciente]) -> int:
    """Acumula el total de atenciones urgentes aplicando tubería filter -> map -> reduce."""
    urgentes = filter(lambda p: p.es_urgente(), pacientes)
    conteo_unitario = map(lambda _: 1, urgentes)
    return reduce(lambda acumulado, valor: acumulado + valor, conteo_unitario, 0)
