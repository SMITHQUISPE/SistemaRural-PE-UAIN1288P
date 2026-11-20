# ============================================================================
# MÓDULO: modelo.py
# Descripción: Entidades del dominio clínico con encapsulamiento estricto y
#              tratamiento seguro de datos personales (Ley N.° 29733).
# ============================================================================
import hashlib
from abc import ABC, abstractmethod


class ErrorSistemaSalud(Exception):
    """Excepción base para errores de negocio en SistemaRural-PE."""
    pass


class DatosInvalidosError(ErrorSistemaSalud):
    """Se lanza cuando los datos ingresados incumplen reglas de validación."""
    pass


class RegistroDuplicadoError(ErrorSistemaSalud):
    """Se lanza cuando se intenta registrar un DNI ya indexado."""
    pass


class Persona(ABC):
    """Clase base abstracta que protege la identidad del ciudadano (Ley N.° 29733)."""

    def __init__(self, dni: str, nombre: str, telefono: str):
        self.set_dni(dni)
        self.set_nombre(nombre)
        self.set_telefono(telefono)

    def set_dni(self, dni: str) -> None:
        dni_limpio = dni.strip()
        if len(dni_limpio) != 8 or not dni_limpio.isdigit():
            raise DatosInvalidosError("El DNI debe contener exactamente 8 dígitos numéricos.")
        # Nunca se almacena ni expone el DNI en texto plano: se aplica hash SHA-256
        self.__dni_hash = hashlib.sha256(dni_limpio.encode("utf-8")).hexdigest()[:12]

    def set_nombre(self, nombre: str) -> None:
        nombre_limpio = nombre.strip()
        if len(nombre_limpio) < 3:
            raise DatosInvalidosError("El nombre completo debe tener al menos 3 caracteres.")
        self.__nombre = nombre_limpio

    def set_telefono(self, telefono: str) -> None:
        tel_limpio = telefono.strip()
        if len(tel_limpio) != 9 or not tel_limpio.isdigit():
            raise DatosInvalidosError("El teléfono debe contener 9 dígitos numéricos.")
        # Enmascaramiento parcial de teléfono para evitar exposición sensible
        self.__telefono_protegido = f"*****{tel_limpio[-4:]}"

    def get_dni_hash(self) -> str:
        return self.__dni_hash

    def get_dni_protegido(self) -> str:
        return f"ID-{self.__dni_hash}"

    def get_nombre(self) -> str:
        return self.__nombre

    def get_telefono_protegido(self) -> str:
        return self.__telefono_protegido

    @abstractmethod
    def obtener_resumen(self) -> str:
        """Método polimórfico implementado por cada subclase concreta."""
        pass


class Paciente(Persona):
    """Representa a un paciente atendido en el Puesto de Salud Rural Santa Rosa."""

    def __init__(self, dni: str, nombre: str, telefono: str, edad: int, comunidad: str, urgente: bool):
        super().__init__(dni, nombre, telefono)
        self.set_edad(edad)
        self.__comunidad = comunidad.strip() or "Chugur Centro"
        self.__urgente = bool(urgente)

    def set_edad(self, edad: int) -> None:
        if not isinstance(edad, int) or not (0 <= edad <= 120):
            raise DatosInvalidosError("La edad debe ser un entero válido entre 0 y 120 años.")
        self.__edad = edad

    def get_edad(self) -> int:
        return self.__edad

    def get_comunidad(self) -> str:
        return self.__comunidad

    def es_urgente(self) -> bool:
        return self.__urgente

    def obtener_resumen(self) -> str:
        prioridad = "URGENTE" if self.__urgente else "REGULAR"
        return (
            f"[{self.get_dni_protegido()}] {self.get_nombre()} | "
            f"{self.__edad} años | {self.__comunidad} | Tel: {self.get_telefono_protegido()} | {prioridad}"
        )
