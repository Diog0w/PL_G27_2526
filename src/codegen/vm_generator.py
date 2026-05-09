from dataclasses import dataclass

from ..parser.semantic import CHARACTER, INTEGER, LOGICAL, REAL


class CodeGenerationError(Exception):
    """Erro durante a geracao de codigo EWVM."""


@dataclass
class Symbol:
    name: str
    type_name: str
    offset: int
    size: int
    dimensions: list
    storage: str


@dataclass
class UnitInfo:
    name: str
    kind: str
    params: list[str]
    return_type: str | None
    statements: list
    symbols: dict[str, Symbol]
    allocations: list[Symbol]


def generate_vm(ast) -> str:
    """Generate EWVM code from the validated tuple AST."""
    return "\n".join(generate_vm_lines(ast)) + "\n"


def generate_vm_lines(ast) -> list[str]:
    return VMGenerator().generate(ast)


class VMGenerator:
    def __init__(self):
        self.functions: dict[str, UnitInfo] = {}
        self.subroutines: dict[str, UnitInfo] = {}
        self._label_counter = 0

    def generate(self, ast) -> list[str]:
        kind, main_program, subprograms = ast
        if kind != "program_file":
            raise CodeGenerationError("AST invalida: esperava program_file")

        main_info = self._build_unit_info(main_program)
        sub_infos = [self._build_unit_info(unit) for unit in subprograms]

        for info in sub_infos:
            if info.kind == "function":
                self.functions[info.name] = info
            elif info.kind == "subroutine":
                self.subroutines[info.name] = info

        code = []
        code.extend(self._allocation_code(main_info))
        code.append("START")
        code.extend(self._generate_statements(main_info.statements, main_info))
        code.append("STOP")

        for info in sub_infos:
            code.append(f"{info.name}:")
            code.extend(self._allocation_code(info))
            code.extend(self._generate_statements(info.statements, info))
            if not _ends_with_return(info.statements):
                code.extend(self._default_return(info))

        return code

    def _build_unit_info(self, unit) -> UnitInfo:
        kind = unit[0]
        if kind == "main_program":
            _, name, statements = unit
            params = []
            return_type = None
        elif kind == "function":
            _, name, params, return_type, statements = unit
            return_type = return_type or INTEGER
        elif kind == "subroutine":
            _, name, params, statements = unit
            return_type = None
        else:
            raise CodeGenerationError(f"Unidade desconhecida: {kind}")

        symbols: dict[str, Symbol] = {}
        allocations: list[Symbol] = []
        next_offset = 0

        if kind == "function":
            result_symbol = Symbol(name, return_type, 0, 1, [], "local")
            symbols[name] = result_symbol
            allocations.append(result_symbol)
            next_offset = 1

        param_count = len(params)
        for index, param in enumerate(params):
            storage = "param_ref" if kind == "subroutine" else "param"
            symbols[param] = Symbol(param, INTEGER, index - param_count, 1, [], storage)

        for statement in statements:
            if statement[0] != "declaration":
                continue
            _kind, _label, type_name, variables = statement
            for variable in variables:
                _vkind, var_name, dimensions = variable
                size = _static_size(dimensions)
                if var_name in symbols:
                    symbol = symbols[var_name]
                    symbol.type_name = type_name
                    symbol.dimensions = list(dimensions)
                    symbol.size = size
                    if dimensions and symbol.storage == "param":
                        symbol.storage = "param_ref"
                    continue

                storage = "global" if kind == "main_program" else "local"
                symbol = Symbol(var_name, type_name, next_offset, size, list(dimensions), storage)
                symbols[var_name] = symbol
                allocations.append(symbol)
                next_offset += size

        return UnitInfo(name, kind, list(params), return_type, statements, symbols, allocations)

    def _allocation_code(self, unit: UnitInfo) -> list[str]:
        code = []
        for symbol in unit.allocations:
            if symbol.size > 1:
                code.append(f"PUSHN {symbol.size}")
            else:
                code.append(_default_value_instruction(symbol.type_name))
        return code

    def _generate_statements(self, statements, unit: UnitInfo) -> list[str]:
        code = []
        for statement in statements:
            code.extend(self._generate_statement(statement, unit))
        return code

    def _generate_statement(self, statement, unit: UnitInfo) -> list[str]:
        kind = statement[0]
        label = statement[1]
        code = self._statement_label(label)

        if kind == "declaration":
            return code + (["NOP"] if label is not None else [])

        if kind == "assignment":
            _kind, _label, target, value = statement
            return code + self._generate_assignment(target, value, unit)

        if kind == "print":
            _kind, _label, items = statement
            return code + self._generate_print(items, unit)

        if kind == "read":
            _kind, _label, items = statement
            return code + self._generate_read(items, unit)

        if kind == "goto":
            _kind, _label, target_label = statement
            return code + [f"JUMP {self._user_label(target_label)}"]

        if kind == "call":
            _kind, _label, name, arguments = statement
            return code + self._generate_subroutine_call(name, arguments, unit)

        if kind == "return":
            return code + self._return_code(unit)

        if kind == "stop":
            return code + ["STOP"]

        if kind == "continue":
            return code + ["NOP"]

        if kind == "if":
            _kind, _label, condition, then_body, else_body = statement
            return code + self._generate_if(condition, then_body, else_body, unit)

        if kind == "do":
            _kind, _label, target_label, variable, start, end, step, body = statement
            return code + self._generate_do(target_label, variable, start, end, step, body, unit)

        raise CodeGenerationError(f"Statement desconhecido: {kind}")

    def _generate_assignment(self, target, value, unit: UnitInfo) -> list[str]:
        target_type = self._reference_type(target, unit)
        value_type = self._expression_type(value, unit)
        value_code = self._generate_expression(value, unit)
        value_code = self._coerce(value_code, value_type, target_type)
        return self._store_reference(target, value_code, unit)

    def _generate_print(self, items, unit: UnitInfo) -> list[str]:
        code = []
        for item in items:
            item_type = self._expression_type(item, unit)
            code.extend(self._generate_expression(item, unit))
            code.append(_write_instruction(item_type))
        code.append("WRITELN")
        return code

    def _generate_read(self, items, unit: UnitInfo) -> list[str]:
        code = []
        for item in items:
            target_type = self._reference_type(item, unit)
            value_code = ["READ"] + _read_conversion(target_type)
            code.extend(self._store_reference(item, value_code, unit))
        return code

    def _generate_subroutine_call(self, name: str, arguments, unit: UnitInfo) -> list[str]:
        if name not in self.subroutines:
            raise CodeGenerationError(f"Subroutine desconhecida: {name}")

        code = []
        for argument in arguments:
            if argument[0] != "reference":
                raise CodeGenerationError(f"Argumento de CALL '{name}' tem de ser uma referencia")
            code.extend(self._generate_address(argument, unit, allow_whole_array=True))
        code.extend([f"PUSHA {name}", "CALL"])
        return code

    def _generate_if(self, condition, then_body, else_body, unit: UnitInfo) -> list[str]:
        end_label = self._new_label("ENDIF")
        code = self._generate_expression(condition, unit)

        if else_body:
            else_label = self._new_label("ELSE")
            code.append(f"JZ {else_label}")
            code.extend(self._generate_statements(then_body, unit))
            code.extend([f"JUMP {end_label}", f"{else_label}:"])
            code.extend(self._generate_statements(else_body, unit))
            code.append(f"{end_label}:")
            return code

        code.append(f"JZ {end_label}")
        code.extend(self._generate_statements(then_body, unit))
        code.append(f"{end_label}:")
        return code

    def _generate_do(self, target_label, variable, start, end, step, body, unit: UnitInfo) -> list[str]:
        start_label = self._new_label("DOSTART")
        end_label = self._new_label("DOEND")
        step = step if step is not None else ("literal", 1)
        comparison = "GE" if _is_negative_literal(step) else "LE"

        control_ref = ("reference", variable, [])
        code = self._store_reference(control_ref, self._generate_expression(start, unit), unit)
        code.append(f"{start_label}:")
        code.extend(self._generate_expression(("binary", comparison, control_ref, end), unit))
        code.append(f"JZ {end_label}")
        code.extend(self._generate_statements(body, unit))
        code.append(f"{self._user_label(target_label)}:")
        increment = ("binary", "+", control_ref, step)
        code.extend(self._generate_assignment(control_ref, increment, unit))
        code.extend([f"JUMP {start_label}", f"{end_label}:"])
        return code

    def _generate_expression(self, expression, unit: UnitInfo) -> list[str]:
        kind = expression[0]

        if kind == "literal":
            return [_literal_instruction(expression[1])]

        if kind == "reference":
            return self._generate_reference(expression, unit)

        if kind == "unary":
            _kind, operator, operand = expression
            operand_type = self._expression_type(operand, unit)
            code = self._generate_expression(operand, unit)
            if operator == "+":
                return code
            if operator == "-":
                if operand_type == REAL:
                    return code + ["PUSHF -1.0", "FMUL"]
                return code + ["PUSHI -1", "MUL"]
            if operator == "NOT":
                return code + ["NOT"]
            raise CodeGenerationError(f"Operador unario desconhecido: {operator}")

        if kind == "binary":
            return self._generate_binary(expression, unit)

        raise CodeGenerationError(f"Expressao desconhecida: {kind}")

    def _generate_binary(self, expression, unit: UnitInfo) -> list[str]:
        _kind, operator, left, right = expression
        left_type = self._expression_type(left, unit)
        right_type = self._expression_type(right, unit)
        left_code = self._generate_expression(left, unit)
        right_code = self._generate_expression(right, unit)

        if operator in {"+", "-", "*", "/", "**"}:
            if operator == "**":
                return self._generate_power(left, right, unit)
            result_type = REAL if REAL in {left_type, right_type} else INTEGER
            left_code = self._coerce(left_code, left_type, result_type)
            right_code = self._coerce(right_code, right_type, result_type)
            return left_code + right_code + [_arithmetic_instruction(operator, result_type)]

        if operator in {"EQ", "NE", "LT", "LE", "GT", "GE"}:
            if left_type in {INTEGER, REAL} and right_type in {INTEGER, REAL}:
                result_type = REAL if REAL in {left_type, right_type} else INTEGER
                left_code = self._coerce(left_code, left_type, result_type)
                right_code = self._coerce(right_code, right_type, result_type)
                return left_code + right_code + _relational_instructions(operator, result_type)
            return left_code + right_code + _relational_instructions(operator, left_type)

        if operator == "AND":
            return left_code + right_code + ["AND"]

        if operator == "OR":
            return left_code + right_code + ["OR"]

        raise CodeGenerationError(f"Operador binario desconhecido: {operator}")

    def _generate_power(self, left, right, unit: UnitInfo) -> list[str]:
        if right[0] != "literal" or not isinstance(right[1], int) or right[1] < 0:
            raise CodeGenerationError("O operador ** so e gerado para expoentes inteiros literais nao negativos")
        exponent = right[1]
        left_type = self._expression_type(left, unit)
        if exponent == 0:
            return ["PUSHF 1.0"] if left_type == REAL else ["PUSHI 1"]

        code = self._generate_expression(left, unit)
        op = "FMUL" if left_type == REAL else "MUL"
        for _ in range(exponent - 1):
            code.extend(self._generate_expression(left, unit))
            code.append(op)
        return code

    def _generate_reference(self, reference, unit: UnitInfo) -> list[str]:
        _kind, name, indices = reference
        symbol = unit.symbols.get(name)

        if not indices:
            if symbol is None:
                raise CodeGenerationError(f"Identificador desconhecido: {name}")
            if symbol.dimensions:
                raise CodeGenerationError(f"Array '{name}' usado sem indices")
            return self._load_symbol(symbol)

        if symbol is not None and symbol.dimensions:
            return self._generate_array_access(reference, unit)

        if name == "MOD":
            if len(indices) != 2:
                raise CodeGenerationError("MOD espera dois argumentos")
            return self._generate_expression(indices[0], unit) + self._generate_expression(indices[1], unit) + ["MOD"]

        if name in self.functions:
            code = []
            for argument in indices:
                code.extend(self._generate_expression(argument, unit))
            code.extend([f"PUSHA {name}", "CALL"])
            return code

        raise CodeGenerationError(f"Referencia desconhecida: {name}")

    def _generate_array_access(self, reference, unit: UnitInfo) -> list[str]:
        return self._generate_address_and_index(reference, unit) + ["LOADN"]

    def _store_reference(self, reference, value_code: list[str], unit: UnitInfo) -> list[str]:
        _kind, name, indices = reference
        symbol = self._lookup_symbol(name, unit)

        if indices:
            return self._generate_address_and_index(reference, unit) + value_code + ["STOREN"]

        if symbol.storage == "global":
            return value_code + [f"STOREG {symbol.offset}"]

        if symbol.storage in {"local", "param"}:
            return value_code + [f"STOREL {symbol.offset}"]

        if symbol.storage == "param_ref":
            return self._generate_address(reference, unit) + value_code + ["STORE 0"]

        raise CodeGenerationError(f"Armazenamento desconhecido para '{name}': {symbol.storage}")

    def _load_symbol(self, symbol: Symbol) -> list[str]:
        if symbol.storage == "global":
            return [f"PUSHG {symbol.offset}"]
        if symbol.storage in {"local", "param"}:
            return [f"PUSHL {symbol.offset}"]
        if symbol.storage == "param_ref":
            return [f"PUSHL {symbol.offset}", "LOAD 0"]
        raise CodeGenerationError(f"Armazenamento desconhecido para '{symbol.name}': {symbol.storage}")

    def _generate_address_and_index(self, reference, unit: UnitInfo) -> list[str]:
        address_code = self._generate_address(reference, unit, base_only=True)
        index_code = self._generate_linear_index(reference, unit)
        return address_code + index_code

    def _generate_address(self, reference, unit: UnitInfo, base_only=False, allow_whole_array=False) -> list[str]:
        _kind, name, indices = reference
        symbol = self._lookup_symbol(name, unit)
        if indices and not base_only and not symbol.dimensions:
            raise CodeGenerationError(f"Identificador '{name}' nao e array")
        if not indices and symbol.dimensions and not allow_whole_array:
            raise CodeGenerationError(f"Array '{name}' precisa de indices")

        if symbol.storage == "global":
            return ["PUSHGP", f"PUSHI {symbol.offset}", "PADD"]

        if symbol.storage in {"local", "param"}:
            return ["PUSHFP", f"PUSHI {symbol.offset}", "PADD"]

        if symbol.storage == "param_ref":
            return [f"PUSHL {symbol.offset}"]

        raise CodeGenerationError(f"Armazenamento desconhecido para '{name}': {symbol.storage}")

    def _generate_linear_index(self, reference, unit: UnitInfo) -> list[str]:
        _kind, name, indices = reference
        symbol = self._lookup_symbol(name, unit)
        if len(indices) != len(symbol.dimensions):
            raise CodeGenerationError(f"Numero invalido de indices para array '{name}'")

        code = []
        multiplier = 1
        for position, index in enumerate(indices):
            if position > 0:
                previous_dimension = symbol.dimensions[position - 1]
                if previous_dimension[0] != "literal" or not isinstance(previous_dimension[1], int):
                    raise CodeGenerationError(f"Dimensao dinamica em array '{name}' nao suportada na VM")
                multiplier *= previous_dimension[1]

            part = self._generate_expression(index, unit) + ["PUSHI 1", "SUB"]
            if multiplier != 1:
                part.extend([f"PUSHI {multiplier}", "MUL"])
            if code:
                code.extend(part)
                code.append("ADD")
            else:
                code.extend(part)
        return code

    def _expression_type(self, expression, unit: UnitInfo) -> str:
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

        if kind == "reference":
            return self._reference_type(expression, unit)

        if kind == "unary":
            _kind, operator, operand = expression
            return LOGICAL if operator == "NOT" else self._expression_type(operand, unit)

        if kind == "binary":
            _kind, operator, left, right = expression
            if operator in {"+", "-", "*", "/", "**"}:
                left_type = self._expression_type(left, unit)
                right_type = self._expression_type(right, unit)
                return REAL if REAL in {left_type, right_type} else INTEGER
            return LOGICAL

        raise CodeGenerationError(f"Tipo desconhecido para expressao: {kind}")

    def _reference_type(self, reference, unit: UnitInfo) -> str:
        _kind, name, indices = reference
        symbol = unit.symbols.get(name)

        if not indices:
            if symbol is None:
                raise CodeGenerationError(f"Identificador desconhecido: {name}")
            return symbol.type_name

        if symbol is not None and symbol.dimensions:
            return symbol.type_name

        if name == "MOD":
            return INTEGER

        function = self.functions.get(name)
        if function is not None:
            return function.return_type or INTEGER

        raise CodeGenerationError(f"Referencia desconhecida: {name}")

    def _lookup_symbol(self, name: str, unit: UnitInfo) -> Symbol:
        symbol = unit.symbols.get(name)
        if symbol is None:
            raise CodeGenerationError(f"Identificador desconhecido: {name}")
        return symbol

    def _coerce(self, code: list[str], actual: str, expected: str) -> list[str]:
        if actual == expected:
            return code
        if actual == INTEGER and expected == REAL:
            return code + ["ITOF"]
        return code

    def _return_code(self, unit: UnitInfo) -> list[str]:
        if unit.kind == "main_program":
            return ["STOP"]
        if unit.kind == "function":
            result = self._lookup_symbol(unit.name, unit)
            return self._load_symbol(result) + ["RETURN"]
        return ["RETURN"]

    def _default_return(self, unit: UnitInfo) -> list[str]:
        if unit.kind == "function":
            result = self._lookup_symbol(unit.name, unit)
            return self._load_symbol(result) + ["RETURN"]
        if unit.kind == "subroutine":
            return ["RETURN"]
        return []

    def _statement_label(self, label: int | None) -> list[str]:
        return [f"{self._user_label(label)}:"] if label is not None else []

    def _user_label(self, label: int) -> str:
        return f"L{label}"

    def _new_label(self, prefix: str) -> str:
        label = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return label


def _static_size(dimensions) -> int:
    if not dimensions:
        return 1

    size = 1
    for dimension in dimensions:
        if dimension[0] != "literal" or not isinstance(dimension[1], int):
            raise CodeGenerationError("A VM so suporta dimensoes de arrays constantes")
        size *= dimension[1]
    return size


def _default_value_instruction(type_name: str) -> str:
    if type_name == REAL:
        return "PUSHF 0.0"
    if type_name == CHARACTER:
        return 'PUSHS ""'
    return "PUSHI 0"


def _literal_instruction(value) -> str:
    if isinstance(value, bool):
        return f"PUSHI {1 if value else 0}"
    if isinstance(value, int):
        return f"PUSHI {value}"
    if isinstance(value, float):
        return f"PUSHF {value}"
    if isinstance(value, str):
        return f'PUSHS "{_escape_string(value)}"'
    raise CodeGenerationError(f"Literal nao suportado: {value!r}")


def _escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _write_instruction(type_name: str) -> str:
    if type_name == REAL:
        return "WRITEF"
    if type_name == CHARACTER:
        return "WRITES"
    return "WRITEI"


def _read_conversion(type_name: str) -> list[str]:
    if type_name == REAL:
        return ["ATOF"]
    if type_name == CHARACTER:
        return []
    return ["ATOI"]


def _arithmetic_instruction(operator: str, type_name: str) -> str:
    integer_ops = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV",
    }
    real_ops = {
        "+": "FADD",
        "-": "FSUB",
        "*": "FMUL",
        "/": "FDIV",
    }
    return (real_ops if type_name == REAL else integer_ops)[operator]


def _relational_instructions(operator: str, type_name: str) -> list[str]:
    if operator == "EQ":
        return ["EQUAL"]
    if operator == "NE":
        return ["EQUAL", "NOT"]

    integer_ops = {
        "LT": "INF",
        "LE": "INFEQ",
        "GT": "SUP",
        "GE": "SUPEQ",
    }
    real_ops = {
        "LT": "FINF",
        "LE": "FINFEQ",
        "GT": "FSUP",
        "GE": "FSUPEQ",
    }
    return [(real_ops if type_name == REAL else integer_ops)[operator]]


def _is_negative_literal(expression) -> bool:
    if expression[0] == "literal":
        return isinstance(expression[1], (int, float)) and expression[1] < 0
    if expression[0] == "unary" and expression[1] == "-" and expression[2][0] == "literal":
        return isinstance(expression[2][1], (int, float)) and expression[2][1] > 0
    return False


def _ends_with_return(statements) -> bool:
    for statement in reversed(statements):
        if statement[0] != "declaration":
            return statement[0] == "return"
    return False
