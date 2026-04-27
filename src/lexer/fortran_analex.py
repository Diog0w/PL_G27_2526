import re

from ply import lex


literals = (
    ",",
    "(",
    ")",
    "+",
    "-",
    "*",
    "/",
    "=",
    ":",
)


tokens = (
    "ID",
    "LABEL",
    "INTEGER",
    "REAL",
    "STRING",
    "POWER",
    "NEWLINE",
    "PROGRAM",
    "END",
    "INTEGER_TYPE",
    "REAL_TYPE",
    "LOGICAL_TYPE",
    "CHARACTER_TYPE",
    "IF",
    "THEN",
    "ELSE",
    "ENDIF",
    "DO",
    "CONTINUE",
    "GOTO",
    "PRINT",
    "READ",
    "FUNCTION",
    "SUBROUTINE",
    "RETURN",
    "STOP",
    "CALL",
    "TRUE",
    "FALSE",
    "AND",
    "OR",
    "NOT",
    "EQ",
    "NE",
    "LT",
    "LE",
    "GT",
    "GE",
)


def _emit_token(t):
    # O lexer usa esta flag para decidir se um numero no inicio da linha deve
    # ser tratado como LABEL ou como INTEGER normal.
    t.lexer.at_line_start = False
    return t


def t_STRING(t):
    r"'([^'\n]|'')*'|\"([^\"\n]|\"\")*\""
    return _emit_token(t)


def t_PROGRAM(t):
    r"\bprogram\b"
    return _emit_token(t)


def t_END(t):
    r"\bend\b"
    return _emit_token(t)


def t_INTEGER_TYPE(t):
    r"\binteger\b"
    return _emit_token(t)


def t_REAL_TYPE(t):
    r"\breal\b"
    return _emit_token(t)


def t_LOGICAL_TYPE(t):
    r"\blogical\b"
    return _emit_token(t)


def t_CHARACTER_TYPE(t):
    r"\bcharacter\b"
    return _emit_token(t)


def t_IF(t):
    r"\bif\b"
    return _emit_token(t)


def t_THEN(t):
    r"\bthen\b"
    return _emit_token(t)


def t_ELSE(t):
    r"\belse\b"
    return _emit_token(t)


def t_ENDIF(t):
    r"\bendif\b"
    return _emit_token(t)


def t_DO(t):
    r"\bdo\b"
    return _emit_token(t)


def t_CONTINUE(t):
    r"\bcontinue\b"
    return _emit_token(t)


def t_GOTO(t):
    r"\bgoto\b"
    return _emit_token(t)


def t_PRINT(t):
    r"\bprint\b"
    return _emit_token(t)


def t_READ(t):
    r"\bread\b"
    return _emit_token(t)


def t_FUNCTION(t):
    r"\bfunction\b"
    return _emit_token(t)


def t_SUBROUTINE(t):
    r"\bsubroutine\b"
    return _emit_token(t)


def t_RETURN(t):
    r"\breturn\b"
    return _emit_token(t)


def t_STOP(t):
    r"\bstop\b"
    return _emit_token(t)


def t_CALL(t):
    r"\bcall\b"
    return _emit_token(t)


def t_TRUE(t):
    r"\.true\."
    return _emit_token(t)


def t_FALSE(t):
    r"\.false\."
    return _emit_token(t)


def t_AND(t):
    r"\.and\."
    return _emit_token(t)


def t_OR(t):
    r"\.or\."
    return _emit_token(t)


def t_NOT(t):
    r"\.not\."
    return _emit_token(t)


def t_EQ(t):
    r"\.eq\."
    return _emit_token(t)


def t_NE(t):
    r"\.ne\."
    return _emit_token(t)


def t_LT(t):
    r"\.lt\."
    return _emit_token(t)


def t_LE(t):
    r"\.le\."
    return _emit_token(t)


def t_GT(t):
    r"\.gt\."
    return _emit_token(t)


def t_GE(t):
    r"\.ge\."
    return _emit_token(t)


t_POWER = r"\*\*"


def t_REAL(t):
    r"(?:\d+\.\d*|\.\d+)(?:[eEdD][+-]?\d+)?|\d+[eEdD][+-]?\d+"
    return _emit_token(t)


def t_INTEGER(t):
    r"\d+"
    # Em free-form, aceitamos labels numericos no inicio da linha, por exemplo:
    # 10 CONTINUE
    if getattr(t.lexer, "at_line_start", False):
        remainder = t.lexer.lexdata[t.lexer.lexpos :]
        if remainder and remainder[0] in " \t":
            t.type = "LABEL"
    return _emit_token(t)


def t_ID(t):
    r"\b[A-Za-z](?:[A-Za-z0-9_])*\b"
    return _emit_token(t)


t_ignore_COMMENT = r"![^\n]*"


def t_NEWLINE(t):
    r"\n+"
    # Cada quebra de linha reposiciona o lexer para um novo "inicio de linha".
    t.lexer.lineno += len(t.value)
    t.lexer.at_line_start = True
    t.value = "\n"
    return t


t_ignore = " \t\r"


def find_column(text: str, token) -> int:
    # O PLY guarda a posicao absoluta no ficheiro; esta funcao converte essa
    # posicao em coluna dentro da linha atual para melhorar as mensagens de erro.
    line_start = text.rfind("\n", 0, token.lexpos) + 1
    return token.lexpos - line_start + 1


def t_error(t):
    column = find_column(t.lexer.lexdata, t)
    raise SyntaxError(f"Caractere ilegal {t.value[0]!r} na linha {t.lineno}, coluna {column}")


def build_lexer():
    lexer = lex.lex(reflags=re.IGNORECASE)
    lexer.lineno = 1
    # Comecamos sempre a ler o ficheiro como se estivessemos no inicio da 1a linha.
    lexer.at_line_start = True
    return lexer


def tokenize_source(source: str):
    # Normalizar finais de linha evita diferencas entre ficheiros criados em
    # Windows, macOS ou Linux.
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    lexer = build_lexer()
    lexer.input(normalized)

    parsed_tokens = []
    while True:
        token = lexer.token()
        if token is None:
            break
        parsed_tokens.append(token)

    return parsed_tokens
