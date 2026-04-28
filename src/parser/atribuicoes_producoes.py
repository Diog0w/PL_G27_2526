from __future__ import annotations


def p_assignment(p):
    """
    assignment : reference "=" expression
    """
    # Atribuicao classica: referencia no lado esquerdo, expressao no direito.
    p[0] = ("assignment", p[1], p[3])
