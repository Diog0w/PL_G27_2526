from __future__ import annotations

from .errors import ParserError
from .nodes import DoStatement
from .shared import token_column


def p_do_statement(p):
    """
    do_statement : DO label_number ID "=" expression "," expression do_step_opt terminator statement_items do_end
    """
    # O ciclo DO deste subset fecha com um label repetido antes de CONTINUE.
    end_label_token = p[11]
    end_label = int(end_label_token.value)
    if p[2] != end_label:
        # O parser valida logo que o label de fecho coincide com o de abertura.
        raise ParserError(
            f"Esperava o label {p[2]} a fechar o DO",
            end_label_token.lineno,
            token_column(end_label_token),
        )

    p[0] = DoStatement(
        target_label=p[2],
        variable=p[3].upper(),
        start=p[5],
        end=p[7],
        step=p[8],
        body=p[10],
    )


def p_do_step_opt(p):
    """
    do_step_opt : "," expression
                | empty
    """
    # O passo e opcional; quando nao aparece fica a None.
    p[0] = p[2] if len(p) == 3 else None


def p_do_end(p):
    """
    do_end : LABEL CONTINUE terminator
    """
    # Devolvemos o token do label para ter acesso a linha e coluna.
    p[0] = p.slice[1]
