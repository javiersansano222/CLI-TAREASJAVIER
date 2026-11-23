"""Excepciones propias para que la CLI nunca enseñe un traceback previsible."""


class TareasError(Exception):
    """Base de todos los errores previsibles de la herramienta."""

    codigo_salida = 1


class IANoDisponible(TareasError):
    """Sin clave, sin red o el servidor de IA no responde: las órdenes sin IA siguen."""

    codigo_salida = 4

    @property
    def consejo(self) -> str:
        """Qué puede hacer el usuario sin depender de la IA."""
        return (
            "Qué hacer: revisa «tareas comprobar-ia» y el .env (mira "
            ".env.example). Mientras tanto, las acciones sin IA siguen "
            "funcionando igual."
        )


class ConfigError(TareasError):
    """acciones.json no existe, no es JSON o no cumple el esquema."""

    codigo_salida = 3


class AccionNoValida(ConfigError):
    """Una acción concreta tiene un campo mal: se indica cuál y por qué."""

    def __init__(self, accion: str, campo: str, motivo: str) -> None:
        super().__init__(f"Acción «{accion}», campo «{campo}»: {motivo}")
        self.accion = accion
        self.campo = campo
        self.motivo = motivo
