from __future__ import annotations

from .nodes import Assignment


def p_assignment(p):
    """
    assignment : reference "=" expression
    """
    # Atribuicao classica: referencia no lado esquerdo, expressao no direito.
    p[0] = Assignment(target=p[1], value=p[3])
