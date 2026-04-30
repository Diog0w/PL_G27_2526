from .shared import attach_label


def p_program_file(p):
    """
    program_file : opt_newlines main_program subprogram_items
    """
    # Estrutura global do ficheiro: programa principal + subprogramas.
    # Os NEWLINE finais do ficheiro sao removidos antes do parse.
    p[0] = ("program_file", p[2], p[3])


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
    main_program : PROGRAM ID terminator program_body END
    """
    # O nome fica normalizado em maiusculas, como o resto dos identificadores.
    p[0] = ("main_program", p[2].upper(), p[4])


def p_program_body(p):
    """
    program_body : declaration_items executable_items
    """
    # Em Fortran, as declaracoes aparecem antes das instrucoes executaveis.
    p[0] = p[1] + p[2]


def p_declaration_items_list(p):
    """
    declaration_items : declaration_items declaration_item
    """
    p[0] = p[1] + p[2]


def p_declaration_items_empty(p):
    """
    declaration_items : empty
    """
    p[0] = []


def p_declaration_item_newline(p):
    """
    declaration_item : NEWLINE
    """
    p[0] = []


def p_declaration_item_statement(p):
    """
    declaration_item : opt_label declaration terminator
    """
    p[0] = [attach_label(p[2], p[1])]


def p_executable_items_list(p):
    """
    executable_items : executable_items executable_item
    """
    # Todos os blocos executaveis sao representados como listas simples.
    p[0] = p[1] + p[2]


def p_executable_items_empty(p):
    """
    executable_items : empty
    """
    p[0] = []


def p_executable_item_newline(p):
    """
    executable_item : NEWLINE
    """
    p[0] = []


def p_executable_item_statement(p):
    """
    executable_item : executable_statement
    """
    p[0] = [p[1]]


def p_executable_statement_labeled_line(p):
    """
    executable_statement : opt_label assignment terminator
                         | opt_label print_statement terminator
                         | opt_label read_statement terminator
                         | opt_label goto_statement terminator
                         | opt_label call_statement terminator
                         | opt_label RETURN terminator
                         | opt_label STOP terminator
                         | opt_label CONTINUE terminator
    """
    # RETURN, STOP e CONTINUE nao trazem dados extra, por isso criamos os nos aqui.
    token_type = p.slice[2].type
    if token_type == "RETURN":
        statement = ("return",)
    elif token_type == "STOP":
        statement = ("stop",)
    elif token_type == "CONTINUE":
        statement = ("continue",)
    else:
        statement = p[2]
    # Se a linha tiver label, ele fica associado ao statement final.
    p[0] = attach_label(statement, p[1])


def p_executable_statement_if(p):
    """
    executable_statement : opt_label if_statement
    """
    p[0] = attach_label(p[2], p[1])


def p_executable_statement_do(p):
    """
    executable_statement : opt_label do_statement
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
