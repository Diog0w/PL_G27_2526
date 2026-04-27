from __future__ import annotations

from .nodes import GotoStatement, PrintStatement, ReadStatement


def p_print_statement(p):
    """
    print_statement : PRINT "*" "," print_items_opt
    """
    # Suportamos a forma PRINT *, expr1, expr2, ...
    p[0] = PrintStatement(items=p[4])


def p_print_items_opt(p):
    """
    print_items_opt : expression_list
                    | empty
    """
    p[0] = p[1] if p[1] is not None else []


def p_read_statement(p):
    """
    read_statement : READ "*" "," reference_list
    """
    # READ escreve nas referencias recebidas.
    p[0] = ReadStatement(items=p[4])


def p_reference_list_single(p):
    """
    reference_list : reference
    """
    p[0] = [p[1]]


def p_reference_list_many(p):
    """
    reference_list : reference_list "," reference
    """
    p[0] = p[1] + [p[3]]


def p_goto_statement(p):
    """
    goto_statement : GOTO label_number
    """
    # GOTO guarda apenas o label de destino.
    p[0] = GotoStatement(target_label=p[2])
