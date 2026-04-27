#!/usr/bin/bash

for element in programas_teste/*.f77
do
  echo "$element"
  python3 src/compiler_program.py "$element"
done
