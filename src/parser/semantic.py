from .errors import SemanticError

INTEGER = "INTEGER_TYPE"
REAL = "REAL_TYPE"
LOGICAL = "LOGICAL_TYPE"
CHARACTER = "CHARACTER_TYPE"

NUMERIC_TYPES = {INTEGER, REAL}
RELATIONAL_OPS = {"EQ", "NE", "LT", "LE", "GT", "GE"}
ARITHMETIC_OPS = {"+", "-", "*", "/", "**"}
LOGICAL_OPS = {"AND", "OR"}


class SymbolTable:
    # Tabela de simbolos simples, inspirada nos exemplos das aulas.
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self._symbols: dict[str, dict[str, object]] = {}

    def declare(self, name: str, type_name: str, dimensions=None) -> None:
        if name in self._symbols:
            raise SemanticError(f"Identificador '{name}' declarado mais do que uma vez")
        self._symbols[name] = {
            "type": type_name,
            "dimensions": list(dimensions or []),
        }

    def lookup(self, name: str) -> dict[str, object]:
        symbol = self._symbols.get(name)
        if symbol is None:
            raise SemanticError(f"Identificador '{name}' nao foi declarado")
        return symbol

    def get(self, name: str) -> dict[str, object] | None:
        return self._symbols.get(name)


def validate_program(ast):
    """Validate the tuple AST produced by the parser and return it unchanged."""
    kind, main_program, subprograms = ast
    if kind != "program_file":
        raise SemanticError("AST invalida: esperava program_file")

    functions, subroutines = _collect_subprograms(subprograms)
    context = {
        "functions": functions,
        "subroutines": subroutines,
        "intrinsics": {"MOD": {"return_type": INTEGER, "arity": 2}},
    }

    _validate_unit(main_program, context)
    for unit in subprograms:
        _validate_unit(unit, context)

    return ast


def _collect_subprograms(subprograms):
    functions = {}
    subroutines = {}

    for unit in subprograms:
        kind = unit[0]
        if kind == "function":
            _, name, params, return_type, _statements = unit
            if name in functions or name in subroutines:
                raise SemanticError(f"Subprograma '{name}' declarado mais do que uma vez")
            functions[name] = {
                "return_type": return_type or INTEGER,
                "arity": len(params),
            }
        elif kind == "subroutine":
            _, name, params, _statements = unit
            if name in functions or name in subroutines:
                raise SemanticError(f"Subprograma '{name}' declarado mais do que uma vez")
            subroutines[name] = {"arity": len(params)}
        else:
            raise SemanticError(f"Tipo de subprograma desconhecido: {kind}")

    return functions, subroutines


def _validate_unit(unit, context) -> None:
    kind = unit[0]
    if kind == "main_program":
        _, name, statements = unit
        scope = SymbolTable(name)
    elif kind == "function":
        _, name, _params, return_type, statements = unit
        scope = SymbolTable(name)
        # Em Fortran, atribuir ao nome da funcao define o valor de retorno.
        scope.declare(name, return_type or INTEGER)
    elif kind == "subroutine":
        _, name, _params, statements = unit
        scope = SymbolTable(name)
    else:
        raise SemanticError(f"Unidade de programa desconhecida: {kind}")

    labels = _collect_labels(statements)
    for statement in statements:
        _validate_statement(statement, scope, context, labels)


def _collect_labels(statements) -> set[int]:
    labels: set[int] = set()

    def add_label(label: int | None) -> None:
        if label is None:
            return
        if label in labels:
            raise SemanticError(f"Label '{label}' declarado mais do que uma vez")
        labels.add(label)

    def visit(statement) -> None:
        kind = statement[0]
        label = statement[1]
        add_label(label)

        if kind == "if":
            _kind, _label, _condition, then_body, else_body = statement
            for nested in then_body + else_body:
                visit(nested)
        elif kind == "do":
            _kind, _label, target_label, _var, _start, _end, _step, body = statement
            add_label(target_label)
            for nested in body:
                visit(nested)

    for statement in statements:
        visit(statement)

    return labels


def _validate_statement(statement, scope, context, labels) -> None:
    kind = statement[0]

    if kind == "declaration":
        _kind, _label, type_name, variables = statement
        for variable in variables:
            _vkind, name, dimensions = variable
            for dimension in dimensions:
                dim_type = _infer_expression(dimension, scope, context)
                _expect_type(dim_type, INTEGER, "dimensao de array")
                if dimension[0] == "literal" and dimension[1] <= 0:
                    raise SemanticError(f"Dimensao invalida no array '{name}'")
            scope.declare(name, type_name, dimensions)

    elif kind == "assignment":
        _kind, _label, target, value = statement
        target_type = _infer_target(target, scope, context)
        value_type = _infer_expression(value, scope, context)
        _expect_compatible(target_type, value_type, "atribuicao")

    elif kind == "print":
        _kind, _label, items = statement
        for item in items:
            _infer_expression(item, scope, context)

    elif kind == "read":
        _kind, _label, items = statement
        for item in items:
            _infer_target(item, scope, context)

    elif kind == "goto":
        _kind, _label, target_label = statement
        if target_label not in labels:
            raise SemanticError(f"GOTO aponta para label inexistente: {target_label}")

    elif kind == "call":
        _kind, _label, name, arguments = statement
        subroutine = context["subroutines"].get(name)
        if subroutine is None:
            raise SemanticError(f"Subroutine '{name}' nao foi declarada")
        _expect_arity(name, subroutine["arity"], arguments)
        for argument in arguments:
            _infer_expression(argument, scope, context)

    elif kind == "return":
        return

    elif kind == "stop":
        return

    elif kind == "continue":
        return

    elif kind == "if":
        _kind, _label, condition, then_body, else_body = statement
        condition_type = _infer_expression(condition, scope, context)
        _expect_type(condition_type, LOGICAL, "condicao do IF")
        for nested in then_body + else_body:
            _validate_statement(nested, scope, context, labels)

    elif kind == "do":
        _kind, _label, _target_label, variable, start, end, step, body = statement
        variable_type = scope.lookup(variable)["type"]
        _expect_numeric(variable_type, "variavel de controlo do DO")
        _expect_numeric(_infer_expression(start, scope, context), "inicio do DO")
        _expect_numeric(_infer_expression(end, scope, context), "fim do DO")
        if step is not None:
            _expect_numeric(_infer_expression(step, scope, context), "passo do DO")
        for nested in body:
            _validate_statement(nested, scope, context, labels)

    else:
        raise SemanticError(f"Statement desconhecido: {kind}")


def _infer_expression(expression, scope, context) -> str:
    kind = expression[0]

    if kind == "literal":
        value = expression[1]
        if isinstance(value, bool):
            return LOGICAL
        if isinstance(value, int):
            return INTEGER
        if isinstance(value, float):
            return REAL
        if isinstance(value, str):
            return CHARACTER
        raise SemanticError(f"Literal com tipo desconhecido: {value!r}")

    if kind == "reference":
        return _infer_reference(expression, scope, context)

    if kind == "unary":
        _kind, operator, operand = expression
        operand_type = _infer_expression(operand, scope, context)
        if operator == "NOT":
            _expect_type(operand_type, LOGICAL, "operador NOT")
            return LOGICAL
        _expect_numeric(operand_type, f"operador unario {operator}")
        return operand_type

    if kind == "binary":
        _kind, operator, left, right = expression
        left_type = _infer_expression(left, scope, context)
        right_type = _infer_expression(right, scope, context)

        if operator in ARITHMETIC_OPS:
            _expect_numeric(left_type, f"operador {operator}")
            _expect_numeric(right_type, f"operador {operator}")
            return REAL if REAL in {left_type, right_type} else INTEGER

        if operator in RELATIONAL_OPS:
            if left_type in NUMERIC_TYPES and right_type in NUMERIC_TYPES:
                return LOGICAL
            _expect_compatible(left_type, right_type, f"operador {operator}")
            return LOGICAL

        if operator in LOGICAL_OPS:
            _expect_type(left_type, LOGICAL, f"operador {operator}")
            _expect_type(right_type, LOGICAL, f"operador {operator}")
            return LOGICAL

    raise SemanticError(f"Expressao desconhecida: {kind}")


def _infer_reference(reference, scope, context) -> str:
    _kind, name, indices = reference
    symbol = scope.get(name)

    if not indices:
        if symbol is None:
            raise SemanticError(f"Identificador '{name}' nao foi declarado")
        return symbol["type"]

    if symbol is not None and symbol["dimensions"]:
        _validate_array_indices(name, indices, symbol, scope, context)
        return symbol["type"]

    function = context["functions"].get(name) or context["intrinsics"].get(name)
    if function is not None:
        _expect_arity(name, function["arity"], indices)
        for argument in indices:
            _infer_expression(argument, scope, context)
        return function["return_type"]

    if symbol is not None:
        raise SemanticError(f"Identificador '{name}' nao e array nem funcao")

    raise SemanticError(f"Identificador '{name}' nao foi declarado")


def _infer_target(reference, scope, context) -> str:
    _kind, name, indices = reference
    symbol = scope.lookup(name)

    if not indices:
        return symbol["type"]

    if not symbol["dimensions"]:
        raise SemanticError(f"Identificador '{name}' nao e array")

    _validate_array_indices(name, indices, symbol, scope, context)

    return symbol["type"]


def _validate_array_indices(name, indices, symbol, scope, context) -> None:
    if len(indices) != len(symbol["dimensions"]):
        raise SemanticError(f"Numero invalido de indices para array '{name}'")
    for index in indices:
        index_type = _infer_expression(index, scope, context)
        _expect_type(index_type, INTEGER, f"indice do array '{name}'")


def _expect_arity(name: str, arity: int, arguments) -> None:
    if len(arguments) != arity:
        raise SemanticError(
            f"Numero invalido de argumentos em '{name}': esperado {arity}, obtido {len(arguments)}"
        )


def _expect_type(actual: str, expected: str, context: str) -> None:
    if actual != expected:
        raise SemanticError(f"Tipo invalido em {context}: esperado {expected}, obtido {actual}")


def _expect_numeric(actual: str, context: str) -> None:
    if actual not in NUMERIC_TYPES:
        raise SemanticError(f"Tipo invalido em {context}: esperado numerico, obtido {actual}")


def _expect_compatible(expected: str, actual: str, context: str) -> None:
    if expected == actual:
        return
    if expected == REAL and actual == INTEGER:
        return
    raise SemanticError(f"Tipos incompativeis em {context}: esperado {expected}, obtido {actual}")
