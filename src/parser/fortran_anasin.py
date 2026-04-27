import ply.yacc as yacc

from ..lexer.fortran_analex import tokenize_source, tokens
from .errors import ParserError
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


class _TokenStream:
    # Adaptador simples: o yacc espera um objeto com metodo token().
    def __init__(self, token_list):
        self._iterator = iter(token_list)

    def token(self):
        return next(self._iterator, None)


def _trim_trailing_newlines(token_list):
    # Os NEWLINE no fim do ficheiro nao trazem informacao sintatica.
    # Se os deixarmos entrar na gramatica final, competem com a regra que
    # aceita linhas em branco entre subprogramas e criam um conflito
    # shift/reduce desnecessario.
    trimmed = list(token_list)
    while trimmed and trimmed[-1].type == "NEWLINE":
        trimmed.pop()
    return trimmed


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

    def parse(self, tokens, source: str):
        # Guardamos o texto normalizado para calcular colunas corretas.
        normalized = source.replace("\r\n", "\n").replace("\r", "\n")
        set_current_source(normalized)
        token_stream = _TokenStream(_trim_trailing_newlines(tokens))
        return _parser.parse(input="", lexer=None, tokenfunc=token_stream.token, tracking=True)


def parse_source(source: str):
    # Fluxo direto: codigo fonte -> tokens -> AST.
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    token_list = tokenize_source(normalized)
    return FortranParser().parse(token_list, normalized)


def parse_tokens(tokens, source: str):
    # Usado quando os tokens ja foram produzidos antes.
    return FortranParser().parse(tokens, source)


def rec_Parser(input_string: str):
    # Nome mantido por compatibilidade com o estilo do trabalho de Pascal.
    print("==================COMPILACAO INICIADA==================")
    return parse_source(input_string)
