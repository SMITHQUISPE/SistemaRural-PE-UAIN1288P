# ============================================================================
# MÓDULO: interfaz_eventos.py
# Descripción: Interfaz gráfica de escritorio Tkinter orientada a eventos con
#              manejo controlado de excepciones y diseño visual limpio.
# ============================================================================
import tkinter as tk
from tkinter import messagebox
from modelo import ErrorSistemaSalud
from patrones import GestorBaseDatos, FabricaPersonas
from servicios_funcionales import (
    filtrar_urgencias_adultos_mayores,
    generar_reporte_anonimizado,
    calcular_total_urgencias
)


class AplicacionSistemaRural:
    """Controlador principal de eventos de usuario en Tkinter."""

    def __init__(self, root: tk.Tk):
        self.db = GestorBaseDatos()
        self.root = root
        self.root.title("SistemaRural-PE v1.0 | Puesto de Salud Santa Rosa (Chugur)")
        self.root.geometry("500x470")
        self.root.configure(bg="#F1F5F9")
        self.root.resizable(False, False)

        # Encabezado institucional
        header = tk.Frame(root, bg="#1B365D", height=48)
        header.pack(fill="x")
        tk.Label(
            header,
            text="SistemaRural-PE | Puesto de Salud Santa Rosa (Chugur)",
            bg="#1B365D", fg="white", font=("Segoe UI", 10, "bold")
        ).pack(pady=12)

        contenedor = tk.Frame(root, bg="#F1F5F9", padx=24, pady=12)
        contenedor.pack(fill="both", expand=True)

        self.ent_dni = self._crear_campo(contenedor, "DNI Ficticio (8 dígitos):")
        self.ent_nombre = self._crear_campo(contenedor, "Nombres y Apellidos:")
        self.ent_tel = self._crear_campo(contenedor, "Teléfono (9 dígitos):")
        self.ent_edad = self._crear_campo(contenedor, "Edad (años):")
        self.ent_comunidad = self._crear_campo(contenedor, "Comunidad / Caserío:")

        self.var_urgente = tk.BooleanVar()
        tk.Checkbutton(
            contenedor, text="Atención de Urgencia (Prioridad Clínica)",
            variable=self.var_urgente, bg="#F1F5F9", fg="#1E293B",
            font=("Segoe UI", 9, "bold"), activebackground="#F1F5F9"
        ).pack(anchor="w", pady=(6, 10))

        # Botones de acción
        frame_botones = tk.Frame(contenedor, bg="#F1F5F9")
        frame_botones.pack(fill="x", pady=4)

        tk.Button(
            frame_botones, text="Registrar Paciente", command=self.evento_registrar,
            bg="#065F46", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=14, pady=7, cursor="hand2"
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        tk.Button(
            frame_botones, text="Reporte Urgencias >=60", command=self.evento_reporte,
            bg="#0F4C81", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=14, pady=7, cursor="hand2"
        ).pack(side="right", expand=True, fill="x", padx=(6, 0))

        # Panel de estado y privacidad (Ley N.° 29733)
        self.frame_estado = tk.Frame(contenedor, bg="#E2E8F0", bd=1, relief="solid", padx=10, pady=8)
        self.frame_estado.pack(fill="x", pady=(12, 0))

        self.lbl_estado = tk.Label(
            self.frame_estado, text="Listo para operar.",
            bg="#E2E8F0", fg="#1B365D", font=("Consolas", 9, "bold")
        )
        self.lbl_estado.pack()

        self.lbl_privacidad = tk.Label(
            self.frame_estado,
            text="Privacidad activa (Ley N.° 29733): DNI cifrado SHA-256 y teléfono enmascarado",
            bg="#E2E8F0", fg="#475569", font=("Segoe UI", 7.5, "italic")
        )
        self.lbl_privacidad.pack()

    def _crear_campo(self, parent: tk.Frame, etiqueta: str) -> tk.Entry:
        tk.Label(
            parent, text=etiqueta, bg="#F1F5F9", fg="#1E293B",
            font=("Segoe UI", 8.5, "bold")
        ).pack(anchor="w", pady=(4, 1))
        entrada = tk.Entry(parent, font=("Consolas", 9.5), relief="solid", bd=1)
        entrada.pack(fill="x", ipady=3)
        return entrada

    def evento_registrar(self) -> None:
        """Manejador del evento clic para registro seguro de pacientes."""
        try:
            edad_int = int(self.ent_edad.get().strip())
            datos = {
                "dni": self.ent_dni.get(),
                "nombre": self.ent_nombre.get(),
                "telefono": self.ent_tel.get(),
                "edad": edad_int,
                "comunidad": self.ent_comunidad.get(),
                "urgente": self.var_urgente.get()
            }
            paciente = FabricaPersonas.crear_persona("PACIENTE", datos)
            self.db.registrar_paciente(paciente)
            urg_mayores = len(filtrar_urgencias_adultos_mayores(self.db.listar_pacientes()))
            self._actualizar_banner(
                f"OK: {paciente.get_dni_protegido()} | Urgencias >=60 años: {urg_mayores}",
                bg="#DCFCE7", fg="#166534"
            )
        except ValueError:
            self._actualizar_banner("Error: La edad debe ser un número entero.", bg="#FEE2E2", fg="#991B1B")
        except ErrorSistemaSalud as err:
            self._actualizar_banner(f"Validación: {err}", bg="#FEE2E2", fg="#991B1B")

    def _actualizar_banner(self, texto: str, bg: str, fg: str) -> None:
        self.frame_estado.configure(bg=bg)
        self.lbl_estado.configure(text=texto, bg=bg, fg=fg)
        self.lbl_privacidad.configure(bg=bg, fg=fg)

    def evento_reporte(self) -> None:
        """Manejador del evento clic para generar reporte funcional anonimizado."""
        pacientes = self.db.listar_pacientes()
        total_urg = calcular_total_urgencias(pacientes)
        mayores_urg = filtrar_urgencias_adultos_mayores(pacientes)
        lineas = generar_reporte_anonimizado(mayores_urg)
        detalle = "\n".join(lineas) if lineas else "Sin urgencias en adultos mayores."
        messagebox.showinfo("Reporte Funcional (Ley 29733)", f"Total urgencias: {total_urg}\n\n{detalle}")
