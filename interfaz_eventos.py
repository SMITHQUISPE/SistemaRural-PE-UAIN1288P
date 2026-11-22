from datetime import timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from modelo import Paciente, ErrorSistemaSalud, fecha_hora_peru
from servicios_funcionales import (filtrar_urgencias_adultos_mayores,
    buscar_pacientes_por_texto, generar_reporte_anonimizado,
    calcular_total_urgencias)
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
def generar_opciones_fechas_peru(dias_adelante=14):
    ahora = fecha_hora_peru()
    opciones = []
    for i in range(dias_adelante + 1):
        dia = ahora + timedelta(days=i)
        etiqueta = "HOY" if i == 0 else "MAÑANA" if i == 1 else f"En {i} días"
        opciones.append(f"{dia:%Y-%m-%d} | {etiqueta} - {DIAS_ES[dia.weekday()]} "
                        f"{dia.day:02d}/{MESES_ES[dia.month-1]}/{dia.year}")
    return opciones
def generar_opciones_horas():
    return [f"{h:02d}:{m:02d}" for h in range(7, 19) for m in (0, 30)] + ["19:00"]
class AplicacionSistemaRural:
    def __init__(self, root, repo):
        self.root, self.repo = root, repo
        root.title("SistemaRural-PE | Puesto de Salud Santa Rosa (Chugur, Cajamarca)")
        root.configure(bg="#F1F5F9")
        try: root.state("zoomed")
        except tk.TclError: root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
        self.pacientes_filtrados = []
        self._crear_interfaz()
        self.actualizar_vista()
    def _crear_interfaz(self):
        top = tk.Frame(self.root, bg="#1B365D", pady=8, padx=12)
        top.pack(fill="x")
        tk.Label(top, text="SistemaRural-PE — Puesto de Salud Rural Santa Rosa",
                 bg="#1B365D", fg="white", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.lbl_reloj = tk.Label(top, bg="#0F4C81", fg="#E0F2FE",
                                  font=("Consolas", 10, "bold"), padx=10, pady=4)
        self.lbl_reloj.pack(side="right")
        self._actualizar_reloj()
        cuerpo = tk.Frame(self.root, bg="#F1F5F9", padx=10, pady=8)
        cuerpo.pack(fill="both", expand=True)
        col1 = tk.LabelFrame(cuerpo, text="1. Admisión", bg="#F1F5F9", width=280,
                             padx=8, pady=6, fg="#1B365D")
        col1.pack(side="left", fill="y", padx=(0, 6)); col1.pack_propagate(False)
        self.ent_dni = self._campo(col1, "DNI (8 dígitos):")
        self.ent_nombre = self._campo(col1, "Nombre completo:")
        self.ent_tel = self._campo(col1, "Celular (9 dígitos):")
        self.ent_edad = self._campo(col1, "Edad:")
        self.ent_comunidad = self._campo(col1, "Comunidad / caserío:")
        self.var_urgente = tk.BooleanVar()
        tk.Checkbutton(col1, text="Atención prioritaria", variable=self.var_urgente,
                      bg="#F1F5F9").pack(anchor="w", pady=5)
        self._boton(col1, "Guardar Paciente", self.guardar_paciente, "#065F46")
        self._boton(col1, "🚨 EMERGENCIA URGENTE", self.registrar_emergencia_urgente, "#DC2626")
        self._boton(col1, "Reporte urgencias >= 60", self.ver_reporte, "#0F4C81")
        col2 = tk.LabelFrame(cuerpo, text="2. Citas y áreas de atención", bg="#F1F5F9",
                             fg="#1B365D", padx=8, pady=6)
        col2.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tk.Label(col2, text="Buscar por nombre, ID o comunidad:", bg="#F1F5F9").pack(anchor="w")
        busq = tk.Frame(col2, bg="#F1F5F9"); busq.pack(fill="x", pady=3)
        self.var_busqueda = tk.StringVar()
        self.var_busqueda.trace_add("write", lambda *_: self._filtrar_pacientes())
        tk.Entry(busq, textvariable=self.var_busqueda, font=("Consolas", 10)).pack(side="left", fill="x", expand=True)
        tk.Button(busq, text="Limpiar", command=lambda: self.var_busqueda.set("")).pack(side="right", padx=4)
        tk.Label(col2, text="Paciente seleccionado:", bg="#F1F5F9").pack(anchor="w")
        self.cb_paciente = ttk.Combobox(col2, state="readonly")
        self.cb_paciente.pack(fill="x", pady=3)
        self.cb_paciente.bind("<<ComboboxSelected>>", lambda _: self._cargar_historial_paciente())
        tk.Label(col2, text="Área / personal (11 servicios):", bg="#F1F5F9").pack(anchor="w")
        self.cb_personal = ttk.Combobox(col2, state="readonly")
        self.cb_personal.pack(fill="x", pady=3)
        frame_dt = tk.Frame(col2, bg="#F1F5F9"); frame_dt.pack(fill="x")
        tk.Label(frame_dt, text="Día (Perú):", bg="#F1F5F9").pack(side="left")
        self.cb_dia = ttk.Combobox(frame_dt, state="readonly", values=generar_opciones_fechas_peru(14))
        self.cb_dia.pack(side="left", fill="x", expand=True, padx=4); self.cb_dia.current(0)
        tk.Label(frame_dt, text="Hora:", bg="#F1F5F9").pack(side="left")
        self.cb_hora = ttk.Combobox(frame_dt, state="readonly", width=7, values=generar_opciones_horas())
        self.cb_hora.pack(side="right"); self._seleccionar_proxima_hora()
        botones = tk.Frame(col2, bg="#F1F5F9"); botones.pack(fill="x", pady=5)
        for texto, funcion, color in [("Agendar", self.agendar_cita, "#1E3A8A"),
                ("Confirmar", self.confirmar_cita, "#047857"),
                ("Cancelar", self.cancelar_cita, "#64748B"),
                ("🚨 Emergencia", self.registrar_emergencia_urgente, "#DC2626")]:
            tk.Button(botones, text=texto, command=funcion, bg=color, fg="white").pack(side="left", expand=True, fill="x", padx=2)
        tk.Label(col2, text="Citas (rojo: emergencia, verde: confirmada):", bg="#F1F5F9").pack(anchor="w")
        frame_lista = tk.Frame(col2); frame_lista.pack(fill="both", expand=True)
        self.lista_citas = tk.Listbox(frame_lista, font=("Consolas", 9),
            yscrollcommand=lambda *args: scroll_citas.set(*args))
        scroll_citas = tk.Scrollbar(frame_lista, command=self.lista_citas.yview)
        scroll_citas.pack(side="right", fill="y"); self.lista_citas.pack(fill="both", expand=True, side="left")
        col3 = tk.LabelFrame(cuerpo, text="3. Historia clínica", bg="#F1F5F9",
                             fg="#1B365D", width=340, padx=8, pady=6)
        col3.pack(side="right", fill="y"); col3.pack_propagate(False)
        self.lbl_hc_titulo = tk.Label(col3, text="Seleccione un paciente", bg="#E2E8F0",
                                      fg="#1B365D", justify="left", wraplength=310)
        self.lbl_hc_titulo.pack(fill="x", pady=4)
        tk.Label(col3, text="Signos vitales o diagnóstico:", bg="#F1F5F9").pack(anchor="w")
        self.ent_diagnostico = tk.Entry(col3); self.ent_diagnostico.pack(fill="x", pady=3)
        self._boton(col3, "+ Guardar en Historia Clínica", self.agregar_atencion_hc, "#0F4C81")
        tk.Label(col3, text="Historial cronológico:", bg="#F1F5F9").pack(anchor="w")
        frame_hc = tk.Frame(col3); frame_hc.pack(fill="both", expand=True)
        self.lista_historial = tk.Listbox(frame_hc, font=("Consolas", 8),
            yscrollcommand=lambda *args: scroll_hc.set(*args))
        scroll_hc = tk.Scrollbar(frame_hc, command=self.lista_historial.yview)
        scroll_hc.pack(side="right", fill="y"); self.lista_historial.pack(fill="both", expand=True, side="left")
        self.lbl_estado = tk.Label(self.root, text="Sistema listo | Perú UTC-5 | 11 áreas",
            bg="#E2E8F0", fg="#1B365D", pady=6)
        self.lbl_estado.pack(fill="x", padx=10, pady=5)
    def _boton(self, parent, texto, funcion, color):
        tk.Button(parent, text=texto, command=funcion, bg=color, fg="white",
                  relief="flat", pady=6).pack(fill="x", pady=3)
    def _campo(self, parent, texto):
        tk.Label(parent, text=texto, bg="#F1F5F9").pack(anchor="w", pady=(3, 1))
        entrada = tk.Entry(parent, font=("Consolas", 10)); entrada.pack(fill="x", ipady=3)
        return entrada
    def _actualizar_reloj(self):
        ahora = fecha_hora_peru()
        self.lbl_reloj.configure(text=f"PERÚ UTC-5: {DIAS_ES[ahora.weekday()]} {ahora:%d/%m/%Y %H:%M:%S}")
        self.root.after(1000, self._actualizar_reloj)
    def _seleccionar_proxima_hora(self):
        """Selecciona el siguiente horario válido, incluso si se abre fuera de atención."""
        ahora = fecha_hora_peru()
        minutos = ahora.hour * 60 + ahora.minute
        siguiente = ((minutos // 30) + 1) * 30
        inicio, fin = 7 * 60, 19 * 60
        dia = ahora.date()
        if siguiente < inicio:
            siguiente = inicio
        elif siguiente > fin:
            dia += timedelta(days=1)
            siguiente = inicio
        fecha_objetivo = dia.strftime("%Y-%m-%d")
        opciones = generar_opciones_fechas_peru(30)
        self.cb_dia.configure(values=opciones)
        indice_dia = next((i for i, opcion in enumerate(opciones)
                           if opcion.startswith(fecha_objetivo + " | ")), 0)
        self.cb_dia.current(indice_dia)
        hora = f"{siguiente // 60:02d}:{siguiente % 60:02d}"
        horas = generar_opciones_horas()
        self.cb_hora.current(horas.index(hora) if hora in horas else 0)
    def _filtrar_pacientes(self, hash_preferido=None):
        """Actualiza el selector sin cambiar al paciente que ya estaba seleccionado."""
        anterior = self._paciente_actual()
        hash_objetivo = hash_preferido or (anterior.get_dni_hash() if anterior else None)
        self.pacientes_filtrados = buscar_pacientes_por_texto(
            self.repo.listar_pacientes(), self.var_busqueda.get())
        self.cb_paciente["values"] = [
            f"{p.get_dni_protegido()} - {p.get_nombre()} ({p.get_comunidad()})"
            for p in self.pacientes_filtrados]
        if self.pacientes_filtrados:
            indice = next((i for i, p in enumerate(self.pacientes_filtrados)
                           if p.get_dni_hash() == hash_objetivo), 0)
            self.cb_paciente.current(indice)
            self._cargar_historial_paciente()
        else:
            self.cb_paciente.set("Sin coincidencias")
            self.lista_historial.delete(0, tk.END)
            self.lbl_hc_titulo.configure(text="Ningún paciente seleccionado")
    def _paciente_actual(self):
        indice = self.cb_paciente.current()
        return self.pacientes_filtrados[indice] if 0 <= indice < len(self.pacientes_filtrados) else None
    def _seleccionar_paciente_por_hash(self, dni_hash):
        for indice, paciente in enumerate(self.pacientes_filtrados):
            if paciente.get_dni_hash() == dni_hash:
                self.cb_paciente.current(indice)
                self._cargar_historial_paciente()
                return True
        return False
    def _cargar_historial_paciente(self):
        paciente = self._paciente_actual(); self.lista_historial.delete(0, tk.END)
        if not paciente:
            self.lbl_hc_titulo.configure(text="Ningún paciente seleccionado"); return
        hc = paciente.get_historia_clinica()
        prioridad = "URGENTE" if paciente.es_urgente() else "REGULAR"
        self.lbl_hc_titulo.configure(text=f"HC {hc.get_codigo_hc()} ({prioridad}) | "
            f"{paciente.get_nombre()} | {paciente.get_edad()} años | {paciente.get_comunidad()}")
        for atencion in hc.obtener_atenciones(): self.lista_historial.insert(tk.END, atencion.get_resumen_clinico())
    def actualizar_vista(self):
        self._filtrar_pacientes()
        personal = self.repo.listar_personal()
        self.cb_personal["values"] = [p.obtener_resumen() for p in personal]
        if personal and self.cb_personal.current() < 0: self.cb_personal.current(1 if len(personal)>1 else 0)
        self.lista_citas.delete(0, tk.END)
        for indice, cita in enumerate(self.repo.listar_citas()):
            self.lista_citas.insert(tk.END, cita.obtener_detalle())
            if cita.es_emergencia(): color = ("#FECACA", "#7F1D1D")
            elif cita.get_estado() == "CONFIRMADA": color = ("#DCFCE7", "#166534")
            elif cita.get_estado() == "CANCELADA": color = ("#E2E8F0", "#475569")
            else: color = ("#FEF9C3", "#854D0E")
            self.lista_citas.itemconfig(indice, bg=color[0], fg=color[1])
    def mensaje(self, texto, error=False):
        self.lbl_estado.configure(text=texto, bg="#FEE2E2" if error else "#DCFCE7",
                                  fg="#991B1B" if error else "#166534")
    def guardar_paciente(self):
        """Valida, registra y confirma visualmente el alta del paciente."""
        try:
            dni = self.ent_dni.get().strip()
            nombre = self.ent_nombre.get().strip()
            telefono = self.ent_tel.get().strip()
            edad_texto = self.ent_edad.get().strip()
            comunidad = self.ent_comunidad.get().strip()
            if not dni or not nombre or not telefono or not edad_texto or not comunidad:
                raise ErrorSistemaSalud("Complete todos los campos antes de guardar.")
            try:
                edad = int(edad_texto)
            except ValueError:
                raise ErrorSistemaSalud("La edad debe ser un número entero.")
            paciente = Paciente(dni, nombre, telefono, edad, comunidad,
                                self.var_urgente.get())
            self.repo.registrar_paciente(paciente)
            # Limpiar el formulario solo después de confirmar que se guardó.
            for campo in (self.ent_dni, self.ent_nombre, self.ent_tel,
                          self.ent_edad, self.ent_comunidad):
                campo.delete(0, tk.END)
            self.var_urgente.set(False)
            self.var_busqueda.set("")
            self.actualizar_vista()
            self._seleccionar_paciente_por_hash(paciente.get_dni_hash())
            self.mensaje(f"Paciente guardado correctamente: {paciente.get_nombre()} | "
                         f"HC: {paciente.get_historia_clinica().get_codigo_hc()}")
            messagebox.showinfo("Paciente registrado",
                                f"{paciente.get_nombre()} se guardó correctamente.",
                                parent=self.root)
            self.ent_dni.focus_set()
        except ErrorSistemaSalud as error:
            self.mensaje(f"No se pudo guardar: {error}", True)
            messagebox.showerror("No se pudo guardar el paciente", str(error),
                                 parent=self.root)
        except Exception as error:
            # Evita que un fallo inesperado pase inadvertido al pulsar el botón.
            self.mensaje("Ocurrió un error inesperado al guardar el paciente.", True)
            messagebox.showerror("Error al guardar",
                f"Ocurrió un error inesperado: {type(error).__name__}: {error}",
                parent=self.root)
    def registrar_emergencia_urgente(self):
        try:
            paciente = self._paciente_actual()
            if not paciente: raise ErrorSistemaSalud("Seleccione o registre primero un paciente.")
            motivo = simpledialog.askstring("Emergencia urgente", f"Paciente: {paciente.get_nombre()}\nMotivo:", parent=self.root)
            if motivo is None: return
            personal = self.repo.buscar_personal_por_codigo("URG-08")
            if personal is None: raise ErrorSistemaSalud("No se encuentra el área URG-08.")
            ahora = f"AHORA MISMO ({fecha_hora_peru():%d/%m/%Y %H:%M})"
            cita = self.repo.agendar_cita(ahora, paciente, personal, True, motivo)
            self.actualizar_vista(); self._cargar_historial_paciente()
            self.mensaje(f"EMERGENCIA {cita.get_id_cita()}: {paciente.get_nombre()} derivado directamente a URG-08.", True)
        except ErrorSistemaSalud as error: self.mensaje(f"Error: {error}", True)
    def agendar_cita(self):
        try:
            paciente = self._paciente_actual()
            if paciente is None:
                raise ErrorSistemaSalud("Primero registre o seleccione un paciente.")
            indice = self.cb_personal.current()
            personal_disponible = self.repo.listar_personal()
            if indice < 0 or indice >= len(personal_disponible):
                raise ErrorSistemaSalud("Seleccione un área de atención.")
            personal = personal_disponible[indice]
            seleccion_dia = self.cb_dia.get().strip()
            hora = self.cb_hora.get().strip()
            if not seleccion_dia or " | " not in seleccion_dia or not hora:
                raise ErrorSistemaSalud("Seleccione una fecha y una hora válidas.")
            fecha = seleccion_dia.split(" | ", 1)[0].strip()
            cita = self.repo.agendar_cita(f"{fecha} {hora}", paciente, personal)
            self.actualizar_vista()
            self._cargar_historial_paciente()
            self.mensaje(f"Cita {cita.get_id_cita()} agendada para {paciente.get_nombre()}.")
            messagebox.showinfo("Cita agendada",
                f"{cita.get_id_cita()}\nPaciente: {paciente.get_nombre()}\n"
                f"Área: {personal.get_area()}\nFecha y hora: {fecha} {hora}",
                parent=self.root)
        except ErrorSistemaSalud as error:
            self.mensaje(f"No se pudo agendar: {error}", True)
            messagebox.showerror("No se pudo agendar la cita", str(error), parent=self.root)
        except Exception as error:
            self.mensaje("Ocurrió un error inesperado al agendar.", True)
            messagebox.showerror("Error al agendar",
                f"{type(error).__name__}: {error}", parent=self.root)
    def confirmar_cita(self):
        self._cambiar_estado("CONFIRMADA")
    def cancelar_cita(self):
        self._cambiar_estado("CANCELADA")
    def _cambiar_estado(self, estado):
        seleccion = self.lista_citas.curselection()
        if not seleccion:
            self.mensaje("Seleccione una cita de la lista antes de continuar.", True)
            messagebox.showwarning("Seleccione una cita",
                "Haga clic sobre una cita de la lista y vuelva a pulsar el botón.",
                parent=self.root)
            return
        try:
            indice = int(seleccion[0])
            citas = self.repo.listar_citas()
            if indice < 0 or indice >= len(citas):
                raise ErrorSistemaSalud("La selección ya no es válida. Actualice la lista.")
            cita = self.repo.cambiar_estado_cita(indice, estado)
            id_actualizado = cita.get_id_cita()
            self.actualizar_vista()
            for fila, elemento in enumerate(self.repo.listar_citas()):
                if elemento.get_id_cita() == id_actualizado:
                    self.lista_citas.selection_set(fila)
                    self.lista_citas.see(fila)
                    break
            self._cargar_historial_paciente()
            self.mensaje(f"Cita {cita.get_id_cita()} {cita.get_estado()}.", estado == "CANCELADA")
            messagebox.showinfo("Estado actualizado",
                f"La cita {cita.get_id_cita()} ahora está: {cita.get_estado()}.",
                parent=self.root)
        except ErrorSistemaSalud as error:
            self.mensaje(f"No se pudo actualizar la cita: {error}", True)
            messagebox.showerror("No se pudo actualizar", str(error), parent=self.root)
        except Exception as error:
            self.mensaje("Ocurrió un error inesperado al actualizar la cita.", True)
            messagebox.showerror("Error al confirmar/cancelar",
                f"{type(error).__name__}: {error}", parent=self.root)
    def agregar_atencion_hc(self):
        try:
            paciente = self._paciente_actual()
            if not paciente: raise ErrorSistemaSalud("Seleccione un paciente.")
            self.repo.agregar_consulta_clinica(paciente, self.ent_diagnostico.get(), paciente.es_urgente())
            self.ent_diagnostico.delete(0, tk.END); self._cargar_historial_paciente()
            self.mensaje(f"Atención guardada en la Historia Clínica de {paciente.get_nombre()}.")
        except ErrorSistemaSalud as error: self.mensaje(f"Error: {error}", True)
    def ver_reporte(self):
        pacientes = self.repo.listar_pacientes(); total = calcular_total_urgencias(pacientes)
        mayores = filtrar_urgencias_adultos_mayores(pacientes)
        texto = "\n".join(generar_reporte_anonimizado(mayores)) or "No hay urgencias en adultos mayores."
        messagebox.showinfo("Reporte anonimizado", f"Total de urgencias: {total}\nUrgencias en adultos mayores: {len(mayores)}\n\n{texto}")

