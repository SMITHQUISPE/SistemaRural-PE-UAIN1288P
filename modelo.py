import hashlib
from datetime import datetime, timezone, timedelta
ZONA_PERU = timezone(timedelta(hours=-5))
AREAS_ESTABLECIMIENTO = [
    ("ADM-01", "Admisión y Triaje", "Personal de Admisión y Triaje"),
    ("MED-02", "Medicina General", "Dr. Carlos Mendoza"),
    ("ENF-03", "Enfermería (Inmunizaciones y CRED)", "Lic. Marisol Quispe"),
    ("OBS-04", "Obstetricia y Planificación Familiar", "Obst. Rosaura Vargas"),
    ("ODO-05", "Odontología", "CD. Jorge Salazar"),
    ("NUT-06", "Nutrición", "Lic. Elena Paredes"),
    ("PSI-07", "Psicología / Salud Mental", "Ps. Marco Silva"),
    ("URG-08", "Tópico y Urgencias Básicas", "Equipo de Guardia"),
    ("FAR-09", "Farmacia", "QF. Diana Rojas"),
    ("COM-10", "Salud Comunitaria y Promoción de la Salud", "Tec. Luis Huamán"),
    ("EPI-11", "Vigilancia Epidemiológica y Salud Ambiental", "Ing. Sofía Campos"),
]
def fecha_hora_peru(): return datetime.now(ZONA_PERU)
class ErrorSistemaSalud(Exception): pass
def cifrar_dni(dni):
    dni = str(dni).strip()
    if len(dni) != 8 or not dni.isdigit(): raise ErrorSistemaSalud("El DNI debe tener exactamente 8 dígitos numéricos.")
    return hashlib.sha256(dni.encode("utf-8")).hexdigest()[:10]
def validar_telefono(telefono):
    telefono = str(telefono).strip()
    if len(telefono) != 9 or not telefono.isdigit() or not telefono.startswith("9"):
        raise ErrorSistemaSalud("El celular debe tener 9 dígitos e iniciar con 9.")
    return f"*****{telefono[-4:]}"
class RegistroAtencion:
    def __init__(self, id_atencion, fecha, diagnostico, prioritaria=False):
        self.__id_atencion, self.__fecha = str(id_atencion), str(fecha)
        self.__diagnostico, self.__prioritaria = str(diagnostico).strip(), bool(prioritaria)
    def get_resumen_clinico(self):
        tipo = "URGENTE" if self.__prioritaria else "REGULAR"
        return f"[{self.__id_atencion}] {self.__fecha} | {self.__diagnostico} ({tipo})"
    def es_prioritaria(self): return self.__prioritaria
    def to_dict(self):
        return {"id_atencion": self.__id_atencion, "fecha": self.__fecha,
                "diagnostico": self.__diagnostico, "prioritaria": self.__prioritaria}
class HistoriaClinica:
    def __init__(self, codigo_hc, fecha_apertura, atenciones=None):
        self.__codigo_hc, self.__fecha_apertura = codigo_hc, fecha_apertura
        self.__atenciones = list(atenciones or [])
    def agregar_atencion(self, atencion): self.__atenciones.append(atencion)
    def obtener_atenciones(self): return list(self.__atenciones)
    def quitar_ultima_atencion(self):
        if self.__atenciones: self.__atenciones.pop()
    def get_codigo_hc(self): return self.__codigo_hc
    def get_fecha_apertura(self): return self.__fecha_apertura
class Paciente:
    def __init__(self, dni, nombre, telefono, edad, comunidad, urgente=False,
                 dni_hash_existente=None, tel_protegido_existente=None, historia_existente=None):
        self.__dni_hash = dni_hash_existente or cifrar_dni(dni)
        nombre = str(nombre).strip()
        if len(nombre) < 3 or any(c.isdigit() for c in nombre): raise ErrorSistemaSalud("Ingrese un nombre válido (mínimo 3 caracteres y sin números).")
        self.__nombre = nombre
        self.__telefono_protegido = tel_protegido_existente or validar_telefono(telefono)
        try: edad = int(edad)
        except (ValueError, TypeError): raise ErrorSistemaSalud("La edad debe ser un entero entre 0 y 120 años.")
        if isinstance(edad, bool) or not 0 <= edad <= 120: raise ErrorSistemaSalud("La edad debe estar entre 0 y 120 años.")
        self.__edad = edad
        self.__comunidad = str(comunidad).strip()
        if not self.__comunidad or any(c.isdigit() for c in self.__comunidad): raise ErrorSistemaSalud("Ingrese una comunidad o caserío válida (sin números).")
        self.__urgente = bool(urgente)
        if historia_existente is not None: self.__historia = historia_existente
        else:
            fecha = fecha_hora_peru().strftime("%d/%m/%Y %H:%M")
            atencion = RegistroAtencion(f"AT-{self.__dni_hash[:4].upper()}-1", fecha,
                "Registro en Admisión e Identificación - Apertura de Historia Clínica", self.__urgente)
            self.__historia = HistoriaClinica(f"HC-{self.__dni_hash[:5].upper()}", fecha[:10], [atencion])
    def get_dni_hash(self): return self.__dni_hash
    def get_dni_protegido(self): return f"ID-{self.__dni_hash}"
    def get_nombre(self): return self.__nombre
    def get_telefono_protegido(self): return self.__telefono_protegido
    def get_edad(self): return self.__edad
    def get_comunidad(self): return self.__comunidad
    def es_urgente(self): return self.__urgente
    def marcar_urgente(self, valor=True): self.__urgente = bool(valor)
    def get_historia_clinica(self): return self.__historia
    def obtener_resumen(self):
        estado = "URGENTE" if self.__urgente else "REGULAR"
        return f"{self.get_dni_protegido()} | {self.__nombre} ({self.__edad} años) | {self.__comunidad} | Tel: {self.__telefono_protegido} | {estado}"
class PersonalSalud:
    def __init__(self, codigo_acceso, dni, nombre, colegiatura, area):
        self.__codigo_acceso = str(codigo_acceso).strip().upper()
        self.__dni_hash = cifrar_dni(dni)
        self.__nombre, self.__colegiatura, self.__area = str(nombre).strip(), str(colegiatura).strip(), str(area).strip()
    def get_codigo_acceso(self): return self.__codigo_acceso
    def get_nombre(self): return self.__nombre
    def get_area(self): return self.__area
    def obtener_resumen(self): return f"{self.__codigo_acceso} | {self.__area} | {self.__nombre}"
class Consultorio:
    def __init__(self, codigo, especialidad):
        self.__codigo, self.__especialidad, self.__personal = codigo, especialidad, []
    def agregar_personal(self, profesional): self.__personal.append(profesional)
    def listar_personal(self): return list(self.__personal)
class CitaMedica:
    def __init__(self, id_cita, fecha_hora, paciente, personal, estado="PROGRAMADA", es_emergencia=False):
        self.__id_cita, self.__fecha_hora = id_cita, str(fecha_hora).strip()
        self.__estado = "EMERGENCIA URGENTE" if es_emergencia else estado
        self.__es_emergencia, self.__paciente, self.__personal = bool(es_emergencia), paciente, personal
    def confirmar(self):
        if self.__es_emergencia:
            raise ErrorSistemaSalud("Las emergencias no se confirman como citas; ya tienen atención prioritaria.")
        if self.__estado == "CANCELADA":
            raise ErrorSistemaSalud("No se puede confirmar una cita cancelada.")
        if self.__estado == "CONFIRMADA":
            raise ErrorSistemaSalud("Esta cita ya está confirmada.")
        self.__estado = "CONFIRMADA"
    def cancelar(self):
        if self.__es_emergencia: raise ErrorSistemaSalud("Una emergencia no se puede cancelar desde esta lista.")
        if self.__estado == "CANCELADA": raise ErrorSistemaSalud("La cita ya está cancelada.")
        self.__estado = "CANCELADA"
    def restaurar_estado(self, estado): self.__estado = estado
    def get_id_cita(self): return self.__id_cita
    def get_fecha_hora(self): return self.__fecha_hora
    def get_estado(self): return self.__estado
    def es_emergencia(self): return self.__es_emergencia
    def get_paciente(self): return self.__paciente
    def get_personal(self): return self.__personal
    def obtener_detalle(self):
        prefijo = "[EMERGENCIA URGENTE]" if self.__es_emergencia else f"[{self.__estado}]"
        return f"{prefijo} {self.__id_cita} | {self.__fecha_hora} | Pac: {self.__paciente.get_nombre()} | Área: {self.__personal.get_area()} ({self.__personal.get_nombre()})"
