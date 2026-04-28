from __future__ import annotations

from ..lexer.fortran_analex import find_column

_CURRENT_SOURCE = ""


def set_current_source(source: str) -> None:
    # O parser guarda aqui o texto atual para calcular colunas nos erros.
    global _CURRENT_SOURCE
    _CURRENT_SOURCE = source


def token_column(token) -> int:
    # Sem texto fonte associado, usamos a primeira coluna como fallback.
    if not _CURRENT_SOURCE:
        return 1
    return find_column(_CURRENT_SOURCE, token)


def eof_location() -> tuple[int, int]:
    # Calcula a posicao do fim do ficheiro para erros sem token atual.
    if not _CURRENT_SOURCE:
        return 1, 1

    lines = _CURRENT_SOURCE.split("\n")
    return len(lines), len(lines[-1]) + 1


def attach_label(statement, label: int | None):
    # A AST usa tuplos no estilo dos exemplos das aulas. As producoes de
    # statements criam primeiro o no sem label e este helper insere o label
    # logo a seguir ao tipo do no: ("assignment", label, ...).
    return (statement[0], label, *statement[1:])
