import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lexer import tokenize_source
from src.codegen import generate_vm
from src.parser import parse_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Frontend Fortran 77 em free-form")
    parser.add_argument("path", type=Path, help="Ficheiro Fortran a analisar")
    parser.add_argument("--tokens", action="store_true", help="Mostrar tokens do lexer")
    parser.add_argument("--vm", action="store_true", help="Gerar codigo EWVM")
    parser.add_argument("-o", "--output", type=Path, help="Ficheiro onde guardar o codigo EWVM")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    source = args.path.read_text(encoding="utf-8")

    if args.tokens:
        # Modo de depuracao simples: imprime exatamente os tokens reconhecidos pelo lexer.
        for token in tokenize_source(source):
            print(token)
        return 0

    # Se a analise terminar sem excecoes, o ficheiro esta sintatica e
    # semanticamente valido dentro do subconjunto suportado pelo projeto.
    ast = parse_source(source)

    if args.vm:
        code = generate_vm(ast)
        if args.output is not None:
            args.output.write_text(code, encoding="utf-8")
        else:
            print(code, end="")
        return 0

    print(f"Analise OK: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
