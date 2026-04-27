from __future__ import annotations

from .nodes import ContinueStatement, MainProgram, ProgramFile, ReturnStatement, StopStatement
from .shared import attach_label


def p_program_file(p):
    """
    program_file : opt_newlines main_program subprogram_items
    """
    # Estrutura global do ficheiro: programa principal + subprogramas.
    # Os NEWLINE finais do ficheiro sao removidos antes do parse para evitar
    # ambiguidade com as linhas em branco entre subprogramas.
    p[0] = ProgramFile(main_program=p[2], subprograms=p[3])


def p_opt_newlines(p):
    """
    opt_newlines : opt_newlines NEWLINE
                 | empty
    """
    # Linhas em branco sao permitidas e nao produzem nos no AST.
    p[0] = None


def p_subprogram_items_list(p):
    """
    subprogram_items : subprogram_items subprogram_item
    """
    # Acumula functions e subroutines encontradas apos o programa principal.
    p[0] = p[1] + p[2]


def p_subprogram_items_empty(p):
    """
    subprogram_items : empty
    """
    p[0] = []


def p_subprogram_item_newline(p):
    """
    subprogram_item : NEWLINE
    """
    p[0] = []


def p_subprogram_item_unit(p):
    """
    subprogram_item : function_unit
                    | subroutine_unit
    """
    # Cada item e embrulhado numa lista para simplificar a concatenacao.
    p[0] = [p[1]]


def p_main_program(p):
    """
    main_program : PROGRAM ID terminator statement_items END
    """
    # O nome fica normalizado em maiusculas, como o resto dos identificadores.
    p[0] = MainProgram(name=p[2].upper(), statements=p[4])


def p_statement_items_list(p):
    """
    statement_items : statement_items statement_item
    """
    # Todos os blocos sao representados como listas simples de statements.
    p[0] = p[1] + p[2]


def p_statement_items_empty(p):
    """
    statement_items : empty
    """
    p[0] = []


def p_statement_item_newline(p):
    """
    statement_item : NEWLINE
    """
    p[0] = []


def p_statement_item_statement(p):
    """
    statement_item : statement
    """
    p[0] = [p[1]]


def p_statement_labeled_line(p):
    """
    statement : opt_label declaration terminator
              | opt_label assignment terminator
              | opt_label print_statement terminator
              | opt_label read_statement terminator
              | opt_label goto_statement terminator
              | opt_label call_statement terminator
              | opt_label RETURN terminator
              | opt_label STOP terminator
    """
    # RETURN e STOP nao trazem dados extra, por isso criamos os nos aqui.
    token_type = p.slice[2].type
    if token_type == "RETURN":
        statement = ReturnStatement()
    elif token_type == "STOP":
        statement = StopStatement()
    else:
        statement = p[2]
    # Se a linha tiver label, ele fica associado ao statement final.
    p[0] = attach_label(statement, p[1])


def p_statement_continue(p):
    """
    statement : CONTINUE terminator
    """
    # CONTINUE costuma surgir como alvo do fecho de um DO com label.
    p[0] = ContinueStatement()


def p_statement_if(p):
    """
    statement : opt_label if_statement
    """
    p[0] = attach_label(p[2], p[1])


def p_statement_do(p):
    """
    statement : opt_label do_statement
    """
    p[0] = attach_label(p[2], p[1])


def p_opt_label(p):
    """
    opt_label : LABEL
              | empty
    """
    # Em free-form, um statement pode ou nao comecar com label.
    p[0] = int(p[1]) if p[1] is not None else None


def p_label_number(p):
    """
    label_number : INTEGER
                 | LABEL
    """
    # Aceitamos ambos os tokens para reutilizar a mesma regra.
    p[0] = int(p[1])


def p_terminator(p):
    """
    terminator : NEWLINE
    """
    # As instrucoes simples terminam no fim da linha.
    p[0] = None
