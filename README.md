# Compilador Fortran 77 - Projeto PL

### Grupo 27
- a104266 - Diogo Henrique Costa Ferreira
- a104355 - Rui Miguel Geraldes Branco da Cruz
- a104533 - João Pedro Silva de Carvalho

## Introducao

Este projeto foi desenvolvido no ambito da unidade curricular de Processamento de
Linguagens e tem como objetivo implementar um compilador para um subconjunto de
Fortran 77. O compilador recebe programas escritos em Fortran, realiza analise
lexica, sintatica e semantica, e gera codigo para a maquina virtual EWVM
disponibilizada pelos docentes.

O grupo optou por suportar apenas codigo em formato livre (*free-form*). Esta
decisao simplificou o analisador lexico e permitiu concentrar o trabalho nas
construcoes principais da linguagem: declaracoes, atribuicoes, expressoes,
entrada/saida, condicionais, ciclos, labels, funcoes, subrotinas e arrays.

A implementacao foi feita em Python, usando a biblioteca PLY:

- `ply.lex` para o analisador lexico;
- `ply.yacc` para o analisador sintatico;
- estruturas em tuplos para representar a AST;
- uma fase separada de analise semantica;
- uma fase separada de geracao de codigo EWVM.

Foi escolhida uma arquitetura em fases separadas: o parser constroi uma AST, a
analise semantica valida essa AST, e a geracao de codigo percorre depois essa
estrutura. Esta abordagem segue uma das alternativas apresentadas nas aulas e
tornou o compilador mais modular.

## Organizacao do projeto

```text
PL_G27_2526/
+-- PL2026-projeto.pdf
+-- README.md
+-- programas_teste/
|   +-- hello.f77
|   +-- fatorial.f77
|   +-- somaarr.f77
|   +-- primo.f77
|   +-- conversor.f77
|   +-- subrotina.f77
|   +-- tipos_extra.f77
|   +-- potencia_do_negativos.f77
|   +-- matriz.f77
+-- programas_maquina/
|   +-- hello.out
|   +-- fatorial.out
|   +-- somaarr.out
|   +-- primo.out
|   +-- conversor.out
|   +-- subrotina.out
|   +-- tipos_extra.out
|   +-- potencia_do_negativos.out
|   +-- matriz.out
+-- src/
|   +-- compiler_program.py
|   +-- lexer/
|   +-- parser/
|   +-- codegen/
+-- test_lexer.sh
+-- test_parser.sh
```

A pasta `programas_teste` contem os programas Fortran usados para validar o
compilador. A pasta `programas_maquina` contem o codigo EWVM gerado a partir
desses exemplos.

## Analisador lexico

O analisador lexico esta implementado em `src/lexer/fortran_analex.py`.

O lexer reconhece:

- identificadores;
- literais inteiros, reais, logicos e strings;
- palavras reservadas como `PROGRAM`, `END`, `INTEGER`, `REAL`, `LOGICAL`,
  `CHARACTER`, `IF`, `THEN`, `ELSE`, `ENDIF`, `DO`, `CONTINUE`, `GOTO`,
  `PRINT`, `READ`, `FUNCTION`, `SUBROUTINE`, `RETURN`, `STOP` e `CALL`;
- operadores aritmeticos;
- operadores relacionais Fortran, como `.EQ.`, `.NE.`, `.LT.`, `.LE.`, `.GT.`
  e `.GE.`;
- operadores logicos `.AND.`, `.OR.` e `.NOT.`;
- labels numericos no inicio de linha.

O lexer e case-insensitive, ou seja, aceita tanto `PROGRAM` como `program`.
Internamente, os identificadores sao normalizados para maiusculas nas fases
seguintes.

Como o grupo decidiu suportar apenas free-form, foram assumidas algumas
simplificacoes:

- comentarios apenas com `!`;
- uma instrucao por linha;
- sem continuacao de linha com `&`;
- sem formato fixo classico de Fortran 77;
- labels numericos simplificados, sem limitar aos 5 digitos tradicionais.

Estas limitacoes estao documentadas diretamente no codigo do lexer.

## Analisador sintatico

O parser esta implementado em `src/parser/fortran_anasin.py` e importa as
producoes divididas por ficheiros:

- `programa_producoes.py`;
- `declaracao_producoes.py`;
- `atribuicoes_producoes.py`;
- `io_producoes.py`;
- `funcoes_producoes.py`;
- `ifelse_producoes.py`;
- `ciclos_producoes.py`;
- `expressoes_producoes.py`.

Esta divisao torna a gramatica mais facil de rever e permite associar cada
ficheiro a uma parte concreta da linguagem.

O resultado do parser e uma AST representada por tuplos. Por exemplo:

```python
("assignment", label, target, value)
("if", label, condition, then_body, else_body)
("do", label, target_label, variable, start, end, step, body)
("function", name, params, return_type, statements)
```

Esta opcao evita misturar a analise sintatica com a geracao de codigo e facilita
a analise semantica.

## Gramatica utilizada

A gramatica suportada corresponde a um subconjunto free-form de Fortran 77. De
forma resumida, as principais producoes sao:

```text
program_file
    -> opt_newlines main_program subprogram_items

main_program
    -> PROGRAM ID terminator program_body END

subprogram_items
    -> subprogram_items subprogram_item
     | empty

subprogram_item
    -> function_unit
     | subroutine_unit
     | NEWLINE

program_body
    -> declaration_items executable_items
```

As declaracoes aparecem antes das instrucoes executaveis:

```text
declaration_items
    -> declaration_items declaration_item
     | empty

declaration_item
    -> declaration terminator

declaration
    -> type_spec variable_spec_list

type_spec
    -> INTEGER_TYPE
     | REAL_TYPE
     | LOGICAL_TYPE
     | CHARACTER_TYPE

variable_spec
    -> ID
     | ID "(" expression_list ")"
```

Nesta gramatica, os labels foram reservados para instrucoes executaveis e nao
para declaracoes. Esta decisao simplifica a fronteira entre o bloco de
declaracoes e o bloco de instrucoes: quando o parser encontra um label apos as
declaracoes, sabe que esta a iniciar uma instrucao executavel. Como os labels
sao usados para `DO`, `CONTINUE` e `GOTO`, e nao para identificar declaracoes,
esta simplificacao faz sentido dentro do subconjunto free-form suportado.

As instrucoes executaveis suportadas sao:

```text
executable_statement
    -> opt_label assignment terminator
     | opt_label print_statement terminator
     | opt_label read_statement terminator
     | opt_label goto_statement terminator
     | opt_label call_statement terminator
     | opt_label RETURN terminator
     | opt_label STOP terminator
     | opt_label CONTINUE terminator
     | opt_label if_statement
     | opt_label do_statement
```

A atribuicao e feita sobre uma referencia:

```text
assignment
    -> reference "=" expression

reference
    -> ID
     | ID "(" expression_list_opt ")"
```

A entrada/saida segue as formas usadas nos exemplos do enunciado:

```text
print_statement
    -> PRINT "*" "," print_items_opt

read_statement
    -> READ "*" "," reference_list
```

O `IF` suportado e o `IF` em bloco:

```text
if_statement
    -> IF "(" expression ")" THEN terminator executable_items else_part end_if terminator

else_part
    -> ELSE terminator executable_items
     | empty

end_if
    -> ENDIF
     | END IF
```

O ciclo `DO` segue a forma classica com label de fecho:

```text
do_statement
    -> DO label_number ID "=" expression "," expression do_step_opt terminator
       do_body_items do_end

do_step_opt
    -> "," expression
     | empty

do_end
    -> LABEL CONTINUE terminator
```

As funcoes e subrotinas sao declaradas depois do programa principal:

```text
function_unit
    -> function_prefix FUNCTION ID parameter_name_list_opt terminator program_body END

function_prefix
    -> type_spec
     | empty

subroutine_unit
    -> SUBROUTINE ID parameter_name_list_opt terminator program_body END

call_statement
    -> CALL ID call_arguments_opt
```

As expressoes usam precedencia para resolver a associatividade dos operadores:

```text
expression
    -> expression OR expression
     | expression AND expression
     | NOT expression
     | expression relop expression
     | expression "+" expression
     | expression "-" expression
     | expression "*" expression
     | expression "/" expression
     | expression POWER expression
     | "-" expression
     | "+" expression
     | "(" expression ")"
     | INTEGER
     | REAL
     | STRING
     | TRUE
     | FALSE
     | reference
```

A tabela de precedencias usada e:

```python
precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("right", "NOT"),
    ("nonassoc", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "+", "-"),
    ("left", "*", "/"),
    ("right", "POWER"),
    ("right", "UPLUS", "UMINUS"),
)
```

## Analise semantica

A analise semantica esta implementada em `src/parser/semantic.py`.

Depois de construida a AST, o compilador valida:

- se a AST tem a estrutura esperada;
- se nao existem subprogramas repetidos;
- se variaveis nao sao declaradas mais do que uma vez no mesmo escopo;
- se identificadores usados em expressoes e atribuicoes foram declarados;
- se as atribuicoes respeitam os tipos;
- se condicoes de `IF` sao logicas;
- se expressoes de `DO` sao numericas;
- se os indices de arrays sao inteiros;
- se o numero de indices de um array esta correto;
- se `GOTO` aponta para labels existentes;
- se labels nao sao repetidos;
- se chamadas a funcoes/subrotinas usam o numero correto de argumentos.

Cada unidade de programa possui uma tabela de simbolos propria. A tabela guarda
informacao sobre tipo, dimensoes, tipo de simbolo, offset e tamanho. Estes dados
sao importantes para a geracao posterior de codigo.

A funcao intrinseca `MOD` foi adicionada ao contexto semantico como uma funcao
pre-definida que recebe dois argumentos e devolve um inteiro.

## Geracao de codigo EWVM

A geracao de codigo esta implementada em `src/codegen/vm_generator.py`.

O gerador percorre a AST validada e produz instrucoes para a EWVM. A estrategia
segue o metodo apresentado nas aulas:

- expressoes sao geradas por travessia pos-ordem;
- cada expressao deixa o seu resultado no topo da stack;
- declaracoes reservam espaco na stack;
- atribuicoes calculam o valor e guardam-no com `STOREG`, `STOREL` ou `STOREN`;
- condicionais usam labels, `JZ` e `JUMP`;
- ciclos `DO` usam labels automaticas para inicio e fim;
- arrays usam `PUSHGP`/`PUSHFP`, `PADD`, `LOADN` e `STOREN`;
- funcoes e subrotinas usam labels, `PUSHA`, `CALL` e `RETURN`.

Exemplo simples:

```fortran
PROGRAM HELLO
PRINT *, 'Ola, Mundo!'
END
```

Codigo EWVM gerado:

```text
START
PUSHS "Ola, Mundo!"
WRITES
WRITELN
STOP
```

Para variaveis globais, o codigo reserva as posicoes antes de `START`, para que
o `GP` aponte corretamente para a regiao global:

```text
PUSHI 0
PUSHI 0
START
...
STOP
```

Para arrays, por exemplo `INTEGER NUMS(5)`, e usado:

```text
PUSHN 5
```

E um acesso como `NUMS(I)` gera codigo para calcular o endereco base e o indice
linear:

```text
PUSHGP
PUSHI 0
PADD
PUSHG 5
PUSHI 1
SUB
LOADN
```

### Decisoes de eficiencia na geracao de codigo

Embora nao tenha sido implementada uma fase autonoma de otimizacao global, a
geracao de codigo aplica algumas decisoes locais para evitar instrucoes
redundantes e produzir codigo EWVM mais direto:

- as expressoes sao geradas diretamente em pos-ordem, deixando os resultados na
  stack e evitando variaveis temporarias intermedias;
- arrays com tamanho conhecido sao reservados com `PUSHN n`, em vez de emitir
  uma instrucao de inicializacao para cada posicao;
- declaracoes nao geram instrucoes durante a execucao, exceto a reserva inicial
  de memoria necessaria;
- um `IF` sem `ELSE` gera apenas o salto condicional `JZ` para o fim do bloco,
  sem criar um `JUMP` adicional desnecessario;
- conversoes de tipo so sao emitidas quando necessarias, por exemplo `ITOF`
  apenas quando um inteiro e usado numa operacao real;
- o gerador escolhe instrucoes especificas conforme o tipo da expressao, como
  `ADD`/`FADD`, `DIV`/`FDIV` e `INF`/`FINF`, reduzindo conversoes evitaveis;
- o operador unario `+` nao gera instrucao extra, porque o valor da expressao ja
  se encontra correto;
- quando uma funcao ou subrotina ja termina explicitamente com `RETURN`, nao e
  acrescentado outro `RETURN` implicito;
- a potenciacao com expoente inteiro literal e gerada como uma sequencia direta
  de multiplicacoes, evitando uma chamada auxiliar em tempo de execucao.

Estas decisoes nao substituem um otimizador completo, mas melhoram a qualidade
do codigo VM gerado dentro do subconjunto da linguagem suportado.

## Programas de teste

Foram incluidos os exemplos do enunciado e alguns programas adicionais:

- `hello.f77`: programa minimo com `PRINT`;
- `fatorial.f77`: ciclo `DO` e multiplicacao;
- `somaarr.f77`: arrays, `READ`, `DO` e soma;
- `primo.f77`: condicionais, labels, `GOTO`, `MOD`;
- `conversor.f77`: funcao `CONVRT`;
- `subrotina.f77`: exemplo simples de `SUBROUTINE` e `CALL`.
- `tipos_extra.f77`: `REAL`, `CHARACTER`, operadores logicos, `END IF` e
  `STOP`;
- `potencia_do_negativos.f77`: potenciacao, menos unario e `DO` com passo
  negativo;
- `matriz.f77`: array multidimensional e ciclos `DO` aninhados.

Os ficheiros `.out` correspondentes encontram-se em `programas_maquina/` e podem
ser copiados diretamente para a EWVM.

## Como correr o compilador

Na raiz do projeto:

```bash
cd PL_G27_2526
```

Para executar apenas a analise lexica:

```bash
python3 -B src/compiler_program.py --tokens programas_teste/hello.f77
```

Para executar analise sintatica e semantica:

```bash
python3 -B src/compiler_program.py programas_teste/fatorial.f77
```

Se o programa estiver correto, e apresentada uma mensagem semelhante a:

```text
Analise OK: programas_teste/fatorial.f77
```

Para visualizar a AST produzida pelo parser, sem gerar codigo VM:

```bash
python3 -B -c "from pathlib import Path; from pprint import pprint; from src.parser.fortran_anasin import FortranParser; pprint(FortranParser().parse(Path('programas_teste/fatorial.f77').read_text(encoding='utf-8')))"
```

A AST e apresentada como tuplos e listas Python. Esta opcao e util para
demonstrar a fase intermedia entre os tokens do lexer e o codigo EWVM final.

Para gerar codigo EWVM no terminal:

```bash
python3 -B src/compiler_program.py --vm programas_teste/fatorial.f77
```

Para guardar o codigo EWVM num ficheiro:

```bash
python3 -B src/compiler_program.py --vm programas_teste/fatorial.f77 -o programas_maquina/fatorial.out
```

Para correr os testes existentes:

```bash
bash test_lexer.sh
bash test_parser.sh
```

Caso a biblioteca PLY nao esteja instalada:

```bash
pip install ply
```

## Pontos fortes

Os principais pontos fortes do projeto sao:

- arquitetura modular, com separacao entre lexer, parser, semantica e geracao
  de codigo;
- parser organizado por tipos de producao;
- AST simples em tuplos, semelhante aos exemplos usados nas aulas;
- analise semantica independente da geracao de codigo;
- suporte para os exemplos principais do enunciado;
- suporte para funcoes, subrotinas, arrays, labels e `GOTO`;
- geracao de codigo EWVM funcional para os programas de teste;
- mensagens de erro com linha e coluna para erros sintaticos e lexicos;
- pasta `programas_maquina` com codigo pronto a testar na EWVM.

## Dificuldades encontradas

Uma das principais dificuldades foi decidir ate que ponto devia ser suportado o
Fortran 77 original. O formato fixo tem varias regras historicas, como colunas
especificas, comentarios na primeira coluna e labels com posicoes proprias.
Como o grupo decidiu suportar free-form, essas regras foram simplificadas.

Outra dificuldade foi o tratamento de labels. Em Fortran, um numero pode ser um
literal inteiro ou um label, dependendo da posicao em que aparece. Para resolver
isto, o lexer mantem uma flag que indica se esta no inicio da linha. Quando um
numero aparece no inicio da linha e e seguido de espaco, e tratado como `LABEL`.

Tambem foi necessario tratar o fecho dos ciclos `DO`. A forma:

```fortran
DO 10 I = 1, N
...
10 CONTINUE
```

exige que o parser distinga entre um `CONTINUE` normal e o `CONTINUE` que fecha
o ciclo. Para isso, o corpo do `DO` foi tratado com regras proprias.

Na geracao de codigo, a maior dificuldade foi lidar com funcoes, subrotinas e
arrays. As funcoes usam parametros por valor e devolvem o valor no topo da
stack, enquanto as subrotinas usam argumentos por referencia para permitir que
alterem variaveis do chamador.

## Limitacoes

Apesar de o projeto estar funcional para o subconjunto definido, existem
limitacoes importantes:

- nao suporta o formato fixo completo de Fortran 77;
- nao suporta continuacao de linha com `&`;
- assume uma instrucao por linha;
- nao suporta declaracoes com inicializacao direta;
- nao suporta labels em declaracoes; labels ficam reservados para instrucoes
  executaveis;
- linhas vazias dentro do bloco de declaracoes devem ser evitadas, pois uma
  linha vazia pode marcar a passagem para a zona de instrucoes executaveis;
- nao suporta `DIMENSION`, `COMMON`, `DATA`, `FORMAT` ou `IMPLICIT`;
- nao suporta strings como arrays de caracteres;
- arrays na VM precisam de dimensoes constantes;
- nao ha verificacao dinamica de limites de arrays;
- o operador `**` so e gerado para expoentes inteiros literais nao negativos;
- as subrotinas assumem passagem de argumentos por referencia;
- em chamadas de subrotinas, os argumentos devem ser referencias modificaveis
  como variaveis ou posicoes de arrays, nao literais ou expressoes temporarias;

## Conclusao

O projeto implementa um compilador funcional para um subconjunto free-form de
Fortran 77. A solucao cobre as fases principais de um compilador: analise lexica,
analise sintatica, analise semantica e geracao de codigo para uma maquina
virtual baseada em stack.

A opcao por uma AST e por fases separadas tornou o compilador mais claro e mais
facil de evoluir. O suporte para arrays, labels, `GOTO`, ciclos `DO`, funcoes,
subrotinas e geracao EWVM representa uma base solida e adequada aos objetivos do
trabalho pratico.
