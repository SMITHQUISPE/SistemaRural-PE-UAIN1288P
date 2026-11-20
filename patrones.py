# ============================================================================
# MÓDULO: patrones.py
# Descripción: Implementación de los patrones creacionales Singleton y Factory.
# ============================================================================
from modelo import Persona, Paciente, DatosInvalidosError, RegistroDuplicadoError


class GestorBaseDatos:
    """Patrón Singleton: garantiza una única instancia de repositorio local."""
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.__pacientes = []
            cls._instancia.__dnis_indexados = set()
        return cls._instancia

    def registrar_paciente(self, paciente: Paciente) -> None:
        if paciente.get_dni_hash() in self.__dnis_indexados:
            raise RegistroDuplicadoError("El documento ingresado ya se encuentra registrado.")
        self.__pacientes.append(paciente)
        self.__dnis_indexados.add(paciente.get_dni_hash())

    def listar_pacientes(self) -> list[Paciente]:
        # Retorna una copia superficial para proteger la lista interna contra mutaciones
        return list(self.__pacientes)


class FabricaPersonas:
    """Patrón Factory Method: centraliza la creación polimórfica de entidades."""

    @staticmethod
    def crear_persona(tipo: str, datos: dict) -> Persona:
        tipo_normalizado = tipo.strip().upper()
        if tipo_normalizado == "PACIENTE":
            return Paciente(
                dni=datos["dni"],
                nombre=datos["nombre"],
                telefono=datos["telefono"],
                edad=datos["edad"],
                comunidad=datos.get("comunidad", "Chugur Centro"),
                urgente=datos.get("urgente", False)
            )
        raise DatosInvalidosError(f"Tipo de entidad no soportado: {tipo}")
