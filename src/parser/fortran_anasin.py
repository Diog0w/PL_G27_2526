import ply.yacc as yacc

from ..lexer.fortran_analex import build_lexer, tokens
from .errors import ParserError
from .semantic import validate_program
from .shared import eof_location, set_current_source, token_column

# Regra inicial da gramatica: o ficheiro inteiro deve encaixar aqui.
start = "program_file"

# Importamos os modulos de producoes para que o PLY recolha todas as
# funcoes p_* quando constroi o parser.
from .programa_producoes import *  # noqa: F401,F403
from .declaracao_producoes import *  # noqa: F401,F403
from .atribuicoes_producoes import *  # noqa: F401,F403
from .io_producoes import *  # noqa: F401,F403
from .funcoes_producoes import *  # noqa: F401,F403
from .ifelse_producoes import *  # noqa: F401,F403
from .ciclos_producoes import *  # noqa: F401,F403
from .expressoes_producoes import *  # noqa: F401,F403


def p_empty(p):
    """
    empty :
    """
    # Regra opcional reutilizada por varios modulos.
    p[0] = None


def p_error(p):
    # Uniformizamos aqui as mensagens de erro sintatico.
    if p is not None:
        raise ParserError(
            f"Erro sintatico no token {p.type} ({p.value!r})",
            p.lineno,
            token_column(p),
        )

    line, column = eof_location()
    raise ParserError("Erro sintatico no fim do ficheiro", line, column)


# O parser e construido uma vez e reutilizado nas funcoes abaixo.
_parser = yacc.yacc(debug=False, write_tables=False, start=start)


class FortranParser:
    """PLY YACC parser for the current free-form Fortran subset."""

    def parse(self, source: str):
        # Guardamos o texto normalizado para calcular colunas corretas.
        normalized = source.replace("\r\n", "\n").replace("\r", "\n")
        # O END fecha o programa sem precisar de NEWLINE a seguir.
        # Remover apenas quebras finais evita uma regra extra para linhas vazias no fim.
        parser_input = normalized.rstrip("\n")
        set_current_source(parser_input)
        lexer = build_lexer()
        return _parser.parse(parser_input, lexer=lexer, tracking=True)


def parse_source(source: str):
    # Fluxo direto: codigo fonte -> AST -> validacao semantica.
    ast = FortranParser().parse(source)
    return validate_program(ast)
