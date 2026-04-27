from __future__ import annotations

from .nodes import IfStatement


def p_if_statement(p):
    """
    if_statement : IF "(" expression ")" THEN terminator statement_items else_part ENDIF terminator
    """
    # Aqui tratamos o IF em bloco, nao a forma aritmetica antiga.
    p[0] = IfStatement(condition=p[3], then_body=p[7], else_body=p[8])


def p_else_part(p):
    """
    else_part : ELSE terminator statement_items
              | empty
    """
    # Se nao houver ELSE, devolvemos lista vazia.
    p[0] = p[3] if len(p) == 4 else []
