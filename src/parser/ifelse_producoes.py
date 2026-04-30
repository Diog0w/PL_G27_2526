def p_if_statement(p):
    """
    if_statement : IF "(" expression ")" THEN terminator executable_items else_part end_if terminator
    """
    # Aqui tratamos o IF em bloco, nao a forma aritmetica antiga.
    # Aceitamos tanto ENDIF como END IF.
    p[0] = ("if", p[3], p[7], p[8])


def p_end_if(p):
    """
    end_if : ENDIF
           | END IF
    """
    p[0] = None


def p_else_part(p):
    """
    else_part : ELSE terminator executable_items
              | empty
    """
    # Se nao houver ELSE, devolvemos lista vazia.
    p[0] = p[3] if len(p) == 4 else []
