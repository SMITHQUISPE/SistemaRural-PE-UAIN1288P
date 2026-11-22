from functools import reduce
def filtrar_urgencias_adultos_mayores(pacientes):
    return list(filter(lambda p: p.es_urgente() and p.get_edad() >= 60, pacientes))
def buscar_pacientes_por_texto(pacientes, texto):
    consulta = str(texto).strip().lower()
    if not consulta: return list(pacientes)
    return list(filter(lambda p: consulta in p.get_nombre().lower()
        or consulta in p.get_dni_protegido().lower()
        or consulta in p.get_comunidad().lower(), pacientes))
def generar_reporte_anonimizado(pacientes):
    # No expone nombre, DNI, teléfono, HC ni texto clínico identificable.
    return list(map(lambda p: f"Grupo etario: {'60 años o más' if p.get_edad() >= 60 else 'Menor de 60'} | Atención prioritaria", pacientes))
def calcular_total_urgencias(pacientes):
    return reduce(lambda total, _: total + 1, filter(lambda p: p.es_urgente(), pacientes), 0)
