from __future__ import annotations

from dataclasses import dataclass, field


# Os dataclasses abaixo guardam a estrutura do programa depois do parse.
# Nesta fase nao fazem validacao semantica; apenas representam o que foi lido.
# Sao, na pratica, os nos da AST produzida pelo parser.
@dataclass(slots=True)
class Expression:
    pass


# Grupo de nos usado para literais, variaveis e operadores em expressoes.
@dataclass(slots=True)
class Literal(Expression):
    value: object


@dataclass(slots=True)
class Reference(Expression):
    name: str
    indices: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class UnaryOp(Expression):
    operator: str
    operand: Expression


@dataclass(slots=True)
class BinaryOp(Expression):
    operator: str
    left: Expression
    right: Expression


# Grupo de nos usado para statements, isto e, instrucoes do programa.
@dataclass(slots=True)
class Statement:
    label: int | None = None


@dataclass(slots=True)
class VariableSpec:
    name: str
    dimensions: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class Declaration(Statement):
    type_name: str = ""
    variables: list[VariableSpec] = field(default_factory=list)


@dataclass(slots=True)
class Assignment(Statement):
    target: Reference | None = None
    value: Expression | None = None


@dataclass(slots=True)
class PrintStatement(Statement):
    items: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class ReadStatement(Statement):
    items: list[Reference] = field(default_factory=list)


@dataclass(slots=True)
class CallStatement(Statement):
    name: str = ""
    arguments: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class GotoStatement(Statement):
    target_label: int = 0


@dataclass(slots=True)
class ContinueStatement(Statement):
    pass


@dataclass(slots=True)
class ReturnStatement(Statement):
    pass


@dataclass(slots=True)
class StopStatement(Statement):
    pass


@dataclass(slots=True)
class IfStatement(Statement):
    condition: Expression | None = None
    then_body: list[Statement] = field(default_factory=list)
    else_body: list[Statement] = field(default_factory=list)


@dataclass(slots=True)
class DoStatement(Statement):
    target_label: int = 0
    variable: str = ""
    start: Expression | None = None
    end: Expression | None = None
    step: Expression | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass(slots=True)
class ProgramUnit:
    name: str
    statements: list[Statement] = field(default_factory=list)


# Unidades de programa: programa principal, functions e subroutines.
@dataclass(slots=True)
class MainProgram(ProgramUnit):
    pass


@dataclass(slots=True)
class SubprogramUnit(ProgramUnit):
    parameters: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FunctionUnit(SubprogramUnit):
    return_type: str | None = None


@dataclass(slots=True)
class SubroutineUnit(SubprogramUnit):
    pass


@dataclass(slots=True)
class ProgramFile:
    main_program: MainProgram
    subprograms: list[SubprogramUnit] = field(default_factory=list)
