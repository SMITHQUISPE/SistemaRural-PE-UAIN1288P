import json
import os
from datetime import datetime
from modelo import (Paciente, PersonalSalud, Consultorio, CitaMedica,
                    HistoriaClinica, RegistroAtencion, ErrorSistemaSalud,
                    fecha_hora_peru)
class RepositorioClinico:
    def __init__(self, ruta_archivo="datos_santa_rosa.json"):
        self.__ruta_archivo = ruta_archivo
        self.__pacientes, self.__dnis, self.__personal = [], set(), []
        self.__consultorios, self.__citas = [], []
    def guardar_en_disco(self):
        data = {
            "pacientes": [{"dni_hash": p.get_dni_hash(), "nombre": p.get_nombre(),
                "telefono_protegido": p.get_telefono_protegido(), "edad": p.get_edad(),
                "comunidad": p.get_comunidad(), "urgente": p.es_urgente(),
                "codigo_hc": p.get_historia_clinica().get_codigo_hc(),
                "fecha_apertura": p.get_historia_clinica().get_fecha_apertura(),
                "atenciones": [a.to_dict() for a in p.get_historia_clinica().obtener_atenciones()]}
                for p in self.__pacientes],
            "citas": [{"id_cita": c.get_id_cita(), "fecha_hora": c.get_fecha_hora(),
                "estado": c.get_estado(), "es_emergencia": c.es_emergencia(),
                "paciente_hash": c.get_paciente().get_dni_hash(),
                "personal_codigo": c.get_personal().get_codigo_acceso()} for c in self.__citas]}
        temporal = self.__ruta_archivo + ".tmp"
        try:
            with open(temporal, "w", encoding="utf-8") as archivo:
                json.dump(data, archivo, ensure_ascii=False, indent=2)
            os.replace(temporal, self.__ruta_archivo)
        except OSError as error:
            if os.path.exists(temporal): os.remove(temporal)
            raise ErrorSistemaSalud(f"No se pudo guardar la información: {error}")
    def cargar_desde_disco(self):
        if not os.path.exists(self.__ruta_archivo): return False
        try:
            with open(self.__ruta_archivo, "r", encoding="utf-8") as archivo: data = json.load(archivo)
            pacientes, hashes, mapa = [], set(), {}
            for item in data.get("pacientes", []):
                hash_dni = item["dni_hash"]
                if hash_dni in hashes: raise ValueError("DNI duplicado en archivo")
                atenciones = [RegistroAtencion(a["id_atencion"], a["fecha"], a["diagnostico"], a.get("prioritaria", False)) for a in item.get("atenciones", [])]
                hc = HistoriaClinica(item["codigo_hc"], item["fecha_apertura"], atenciones)
                paciente = Paciente("00000000", item["nombre"], "900000000", int(item["edad"]),
                    item["comunidad"], item.get("urgente", False), hash_dni,
                    item["telefono_protegido"], hc)
                pacientes.append(paciente); hashes.add(hash_dni); mapa[hash_dni] = paciente
            personal = {p.get_codigo_acceso(): p for p in self.__personal}
            citas = []
            for item in data.get("citas", []):
                paciente, profesional = mapa.get(item.get("paciente_hash")), personal.get(item.get("personal_codigo"))
                if paciente is None or profesional is None: continue
                citas.append(CitaMedica(item["id_cita"], item["fecha_hora"], paciente, profesional,
                    item.get("estado", "PROGRAMADA"), item.get("es_emergencia", False)))
            self.__pacientes, self.__dnis, self.__citas = pacientes, hashes, citas
            return True
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            raise ErrorSistemaSalud("El archivo JSON existe, pero está dañado o no tiene el formato esperado. No se sobrescribió.")
    def registrar_paciente(self, paciente, guardar=True):
        if paciente.get_dni_hash() in self.__dnis: raise ErrorSistemaSalud("Este DNI ya está registrado.")
        self.__pacientes.append(paciente); self.__dnis.add(paciente.get_dni_hash())
        try:
            if guardar: self.guardar_en_disco()
        except ErrorSistemaSalud:
            self.__pacientes.pop(); self.__dnis.remove(paciente.get_dni_hash()); raise
    def listar_pacientes(self): return list(self.__pacientes)
    def registrar_personal(self, profesional): self.__personal.append(profesional)
    def listar_personal(self): return list(self.__personal)
    def buscar_personal_por_codigo(self, codigo):
        codigo = str(codigo).strip().upper()
        return next((p for p in self.__personal if p.get_codigo_acceso() == codigo), None)
    def registrar_consultorio(self, consultorio): self.__consultorios.append(consultorio)
    def _guardar_cambio(self, paciente, cita=None, anterior=None):
        try: self.guardar_en_disco()
        except ErrorSistemaSalud:
            if cita is not None: cita.restaurar_estado(anterior)
            raise
    def agendar_cita(self, fecha_hora, paciente, personal, es_emergencia=False, motivo_emergencia="", guardar=True):
        if paciente not in self.__pacientes: raise ErrorSistemaSalud("El paciente no está registrado.")
        if personal not in self.__personal: raise ErrorSistemaSalud("Seleccione un área válida del establecimiento.")
        if es_emergencia and personal.get_codigo_acceso() != "URG-08":
            raise ErrorSistemaSalud("Las emergencias deben derivarse directamente a URG-08.")
        if es_emergencia:
            fecha_hora = f"AHORA MISMO ({fecha_hora_peru():%d/%m/%Y %H:%M})"
            prefijo = "EMG"
        else:
            try: fecha = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M").replace(tzinfo=fecha_hora_peru().tzinfo)
            except ValueError: raise ErrorSistemaSalud("La fecha u hora de la cita no es válida.")
            if fecha <= fecha_hora_peru(): raise ErrorSistemaSalud("La cita debe programarse en una fecha y hora futuras.")
            if not 7 <= fecha.hour <= 19 or (fecha.hour == 19 and fecha.minute != 0) or fecha.minute not in (0, 30):
                raise ErrorSistemaSalud("El horario permitido es de 07:00 a 19:00, cada 30 minutos.")
            prefijo = "CITA"
        numero = 1 + sum(c.get_id_cita().startswith(prefijo + "-") for c in self.__citas)
        cita = CitaMedica(f"{prefijo}-{numero:03d}", fecha_hora, paciente, personal, es_emergencia=es_emergencia)
        anterior_urgencia = paciente.es_urgente()
        if es_emergencia: paciente.marcar_urgente(True); self.__citas.insert(0, cita)
        else: self.__citas.append(cita)
        hc = paciente.get_historia_clinica(); numero_at = len(hc.obtener_atenciones()) + 1
        detalle = (f"EMERGENCIA URGENTE ({cita.get_id_cita()}) -> Pase directo a URG-08 | Motivo: {motivo_emergencia.strip() or 'Atención urgente'}"
                   if es_emergencia else f"Cita ({cita.get_id_cita()}) agendada en {personal.get_area()} ({personal.get_nombre()})")
        hc.agregar_atencion(RegistroAtencion(f"AT-{paciente.get_dni_hash()[:4].upper()}-{numero_at}",
            fecha_hora, detalle, es_emergencia or paciente.es_urgente()))
        if guardar:
            try: self.guardar_en_disco()
            except ErrorSistemaSalud:
                self.__citas.remove(cita); hc.quitar_ultima_atencion()
                paciente.marcar_urgente(anterior_urgencia)
                raise
        return cita
    def cambiar_estado_cita(self, indice, nuevo_estado):
        if not isinstance(indice, int) or not 0 <= indice < len(self.__citas):
            raise ErrorSistemaSalud("Seleccione una cita válida de la lista.")
        if nuevo_estado not in ("CONFIRMADA", "CANCELADA"):
            raise ErrorSistemaSalud("Estado de cita no válido.")
        cita = self.__citas[indice]
        anterior = cita.get_estado()
        if nuevo_estado == "CONFIRMADA":
            cita.confirmar()
        else:
            cita.cancelar()
        paciente = cita.get_paciente()
        hc = paciente.get_historia_clinica()
        numero = len(hc.obtener_atenciones()) + 1
        hc.agregar_atencion(RegistroAtencion(
            f"AT-{paciente.get_dni_hash()[:4].upper()}-{numero}",
            fecha_hora_peru().strftime("%d/%m/%Y %H:%M"),
            f"Estado de {cita.get_id_cita()} actualizado a [{cita.get_estado()}]",
            paciente.es_urgente()))
        try:
            self.guardar_en_disco()
        except ErrorSistemaSalud:
            cita.restaurar_estado(anterior)
            hc.quitar_ultima_atencion()
            raise
        return cita
    def agregar_consulta_clinica(self, paciente, diagnostico, prioritaria):
        diagnostico = str(diagnostico).strip()
        if paciente not in self.__pacientes: raise ErrorSistemaSalud("Seleccione un paciente registrado.")
        if not diagnostico: raise ErrorSistemaSalud("Escriba el diagnóstico o motivo de atención.")
        hc = paciente.get_historia_clinica(); numero = len(hc.obtener_atenciones()) + 1
        hc.agregar_atencion(RegistroAtencion(f"AT-{paciente.get_dni_hash()[:4].upper()}-{numero}",
            fecha_hora_peru().strftime("%d/%m/%Y %H:%M"), diagnostico, prioritaria))
        try: self.guardar_en_disco()
        except ErrorSistemaSalud:
            hc.quitar_ultima_atencion()
            raise
    def listar_citas(self): return list(self.__citas)

