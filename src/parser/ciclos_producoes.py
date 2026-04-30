from .errors import ParserError
from .shared import attach_label, token_column


def p_do_statement(p):
    """
    do_statement : DO label_number ID "=" expression "," expression do_step_opt terminator do_body_items do_end
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

    p[0] = ("do", p[2], p[3].upper(), p[5], p[7], p[8], p[10])


def p_do_body_items_list(p):
    """
    do_body_items : do_body_items do_body_item
    """
    p[0] = p[1] + p[2]


def p_do_body_items_empty(p):
    """
    do_body_items : empty
    """
    p[0] = []


def p_do_body_item_newline(p):
    """
    do_body_item : NEWLINE
    """
    p[0] = []


def p_do_body_item_statement(p):
    """
    do_body_item : do_body_statement
    """
    p[0] = [p[1]]


def p_do_body_statement_labeled_line(p):
    """
    do_body_statement : opt_label assignment terminator
                      | opt_label print_statement terminator
                      | opt_label read_statement terminator
                      | opt_label goto_statement terminator
                      | opt_label call_statement terminator
                      | opt_label RETURN terminator
                      | opt_label STOP terminator
    """
    token_type = p.slice[2].type
    if token_type == "RETURN":
        statement = ("return",)
    elif token_type == "STOP":
        statement = ("stop",)
    else:
        statement = p[2]
    p[0] = attach_label(statement, p[1])


def p_do_body_statement_continue(p):
    """
    do_body_statement : CONTINUE terminator
    """
    # Dentro de um DO, LABEL CONTINUE fica reservado para fechar o ciclo.
    p[0] = ("continue", None)


def p_do_body_statement_if(p):
    """
    do_body_statement : opt_label if_statement
    """
    p[0] = attach_label(p[2], p[1])


def p_do_body_statement_do(p):
    """
    do_body_statement : opt_label do_statement
    """
    p[0] = attach_label(p[2], p[1])


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
