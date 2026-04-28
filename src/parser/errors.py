class FrontendError(Exception):
    """Base error for the Fortran frontend."""

    def __init__(self, message: str, line: int, column: int) -> None:
        # A mensagem final ja sai pronta para ser mostrada no terminal.
        super().__init__(f"{message} (linha {line}, coluna {column})")
        self.message = message
        self.line = line
        self.column = column


class ParserError(FrontendError):
    """Raised when syntactic analysis fails."""


class SemanticError(Exception):
    """Raised when semantic analysis fails."""
