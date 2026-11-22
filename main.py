import os
import tkinter as tk
from modelo import PersonalSalud, Consultorio, AREAS_ESTABLECIMIENTO, fecha_hora_peru
from repositorio import RepositorioClinico
from servicios_funcionales import calcular_total_urgencias
from interfaz_eventos import AplicacionSistemaRural, generar_opciones_fechas_peru
def inicializar_sistema():
    # La base de datos queda junto al programa, no en una carpeta de trabajo aleatoria.
    ruta_datos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_santa_rosa.json")
    repo = RepositorioClinico(ruta_datos)
    consultorio = Consultorio("CONS-SR", "Puesto de Salud Santa Rosa - Chugur")
    for indice, (codigo, area, responsable) in enumerate(AREAS_ESTABLECIMIENTO, 1):
        profesional = PersonalSalud(codigo, f"{indice:08d}", responsable,
                                   f"COL-{1000 + indice}", area)
        repo.registrar_personal(profesional)
        consultorio.agregar_personal(profesional)
    repo.registrar_consultorio(consultorio)
    # No se crean pacientes de demostración: la primera ejecución empieza vacía.
    repo.cargar_desde_disco()
    print(f"Sistema iniciado (Hora Perú: {fecha_hora_peru():%d/%m/%Y %H:%M}).")
    print(f"Áreas: {len(repo.listar_personal())} | Urgencias: "
          f"{calcular_total_urgencias(repo.listar_pacientes())}")
    return repo
if __name__ == "__main__":
    repositorio = inicializar_sistema()
    ventana = tk.Tk()
    AplicacionSistemaRural(ventana, repositorio)
    ventana.mainloop()

