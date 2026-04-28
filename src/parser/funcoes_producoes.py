from __future__ import annotations


def p_function_unit(p):
    """
    function_unit : function_prefix FUNCTION ID parameter_name_list_opt terminator statement_items END
    """
    # Uma FUNCTION pode comecar com um tipo explicito, por exemplo INTEGER FUNCTION.
    p[0] = ("function", p[3].upper(), p[4], p[1], p[6])


def p_function_prefix(p):
    """
    function_prefix : type_spec
                    | empty
    """
    # Quando o tipo nao e escrito, o campo fica a None.
    p[0] = p[1]


def p_subroutine_unit(p):
    """
    subroutine_unit : SUBROUTINE ID parameter_name_list_opt terminator statement_items END
    """
    # SUBROUTINE e uma unidade de programa sem valor de retorno.
    p[0] = ("subroutine", p[2].upper(), p[3], p[5])


def p_parameter_name_list_opt(p):
    """
    parameter_name_list_opt : "(" parameter_name_list ")"
                            | empty
    """
    # Aceita cabecalhos com ou sem lista de parametros.
    p[0] = p[2] if len(p) == 4 else []


def p_parameter_name_list_single(p):
    """
    parameter_name_list : ID
    """
    p[0] = [p[1].upper()]


def p_parameter_name_list_many(p):
    """
    parameter_name_list : parameter_name_list "," ID
    """
    p[0] = p[1] + [p[3].upper()]


def p_call_statement(p):
    """
    call_statement : CALL ID call_arguments_opt
    """
    # CALL cria um statement com o nome da rotina e os argumentos fornecidos.
    p[0] = ("call", p[2].upper(), p[3])


def p_call_arguments_opt(p):
    """
    call_arguments_opt : "(" expression_list_opt ")"
                       | empty
    """
    # Tambem suportamos CALL nome sem parenteses.
    p[0] = p[2] if len(p) == 4 else []
