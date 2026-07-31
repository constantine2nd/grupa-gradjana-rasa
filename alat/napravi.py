# -*- coding: utf-8 -*-
"""Napravi javnu stranicu sajta iz katastarskih podataka. Jedna komanda.

    python3 alat/napravi.py

Redom: gen.py (crta plan i obe stranice) -> translit.py (cirilica u latinicu)
-> standalone.py (uvija javnu u pun HTML i smesta je u koren sajta).

Interna verzija sa imenima ostaje u alat/_izlaz/ i ne komituje se.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

STRANICA = '../inicijativa-za-asfaltiranje-puta-i-opticki-internet.html'
NASLOV = 'Inicijativa za asfaltiranje puta i optički internet — Raša'


def run(*cmd):
    print('$', ' '.join(cmd))
    r = subprocess.run([sys.executable, *cmd])
    if r.returncode:
        sys.exit(f'prekid: {cmd[0]} vratio {r.returncode}')


run('gen.py')
run('translit.py', '_izlaz/provera-parcela.html')
run('translit.py', '_izlaz/katastarski-plan.html')
run('standalone.py', '_izlaz/katastarski-plan.html', STRANICA, NASLOV)
print(f'\ngotovo -> {os.path.abspath(STRANICA)}')
