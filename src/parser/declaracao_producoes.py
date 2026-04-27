from __future__ import annotations

from .nodes import Declaration, VariableSpec


def p_type_spec(p):
    """
    type_spec : INTEGER_TYPE
              | REAL_TYPE
              | LOGICAL_TYPE
              | CHARACTER_TYPE
    """
    # Guardamos o tipo pelo nome do token reconhecido pelo lexer.
    p[0] = p.slice[1].type


def p_declaration(p):
    """
    declaration : type_spec variable_spec_list
    """
    # Uma declaracao junta o tipo e todas as variaveis da linha.
    p[0] = Declaration(type_name=p[1], variables=p[2])


def p_variable_spec_list_single(p):
    """
    variable_spec_list : variable_spec
    """
    p[0] = [p[1]]


def p_variable_spec_list_many(p):
    """
    variable_spec_list : variable_spec_list "," variable_spec
    """
    p[0] = p[1] + [p[3]]


def p_variable_spec_scalar(p):
    """
    variable_spec : ID
    """
    # Variavel simples, sem indices nem dimensoes.
    p[0] = VariableSpec(name=p[1].upper())


def p_variable_spec_array(p):
    """
    variable_spec : ID "(" expression_list ")"
    """
    # Array: as dimensoes ficam guardadas como lista de expressoes.
    p[0] = VariableSpec(name=p[1].upper(), dimensions=p[3])
