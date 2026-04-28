from __future__ import annotations


# A tabela de precedencias ajuda o yacc a decidir como agrupar expressoes.
precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("right", "NOT"),
    ("nonassoc", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "+", "-"),
    ("left", "*", "/"),
    ("right", "POWER"),
    ("right", "UPLUS", "UMINUS"),
)


def p_expression_binop(p):
    """
    expression : expression OR expression
               | expression AND expression
               | expression EQ expression
               | expression NE expression
               | expression LT expression
               | expression LE expression
               | expression GT expression
               | expression GE expression
               | expression "+" expression
               | expression "-" expression
               | expression "*" expression
               | expression "/" expression
               | expression POWER expression
    """
    # O AST guarda um operador simples, independentemente da forma lexica.
    operator_type = p.slice[2].type
    if operator_type == "POWER":
        operator = "**"
    elif operator_type in {"OR", "AND", "EQ", "NE", "LT", "LE", "GT", "GE"}:
        operator = operator_type
    else:
        operator = p[2]
    p[0] = ("binary", operator, p[1], p[3])


def p_expression_not(p):
    """
    expression : NOT expression
    """
    # NOT e um operador unario logico.
    p[0] = ("unary", "NOT", p[2])


def p_expression_uminus(p):
    """
    expression : "-" expression %prec UMINUS
               | "+" expression %prec UPLUS
    """
    # Estes sinais sao unarios, por isso usam precedencia propria.
    p[0] = ("unary", p[1], p[2])


def p_expression_group(p):
    """
    expression : "(" expression ")"
    """
    p[0] = p[2]


def p_expression_integer(p):
    """
    expression : INTEGER
    """
    # Literais passam diretamente para o AST.
    p[0] = ("literal", int(p[1]))


def p_expression_real(p):
    """
    expression : REAL
    """
    # D/d em Fortran corresponde a notacao exponencial real.
    p[0] = ("literal", float(str(p[1]).replace("d", "e").replace("D", "E")))


def p_expression_string(p):
    """
    expression : STRING
    """
    p[0] = ("literal", _decode_string(p[1]))


def p_expression_true_false(p):
    """
    expression : TRUE
               | FALSE
    """
    p[0] = ("literal", p.slice[1].type == "TRUE")


def p_expression_reference(p):
    """
    expression : reference
    """
    # Uma referencia pode aparecer em qualquer contexto de expressao.
    p[0] = p[1]


def p_reference_scalar(p):
    """
    reference : ID
    """
    p[0] = ("reference", p[1].upper(), [])


def p_reference_indexed(p):
    """
    reference : ID "(" expression_list_opt ")"
    """
    # Usamos a mesma estrutura para arrays e referencias indexadas.
    p[0] = ("reference", p[1].upper(), p[3])


def p_expression_list_single(p):
    """
    expression_list : expression
    """
    p[0] = [p[1]]


def p_expression_list_many(p):
    """
    expression_list : expression_list "," expression
    """
    p[0] = p[1] + [p[3]]


def p_expression_list_opt(p):
    """
    expression_list_opt : expression_list
                        | empty
    """
    # Permite listas vazias, por exemplo em CALL sem argumentos.
    p[0] = p[1] if p[1] is not None else []


def _decode_string(lexeme: str) -> str:
    # Em Fortran, a plica/aspas duplica-se para escapar o delimitador.
    quote = lexeme[0]
    body = lexeme[1:-1]
    return body.replace(quote * 2, quote)
