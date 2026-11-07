"""
versao1.py — Ponderada CC08 (Tato), questão A4, Versão 1: SEM sincronização.

Autora: Anne Esther Lins Figueirôa  (D1 = 4, D2 = 3, N = 6)

Produtor (thread do sensor) e consumidor (thread do motor) trocam amostras
por um buffer circular de N posições, coordenados apenas por um contador
compartilhado de posições ocupadas e por espera ocupada (busy waiting).

Para expor a condição de corrida, há um time.sleep(0) entre LER e ESCREVER
o contador. Isso devolve a CPU ao escalonador exatamente no meio do
read-modify-write, simulando a thread sendo interrompida no pior momento.

Uso:
    python3 versao1.py                  # 3 execuções de 20.000 amostras
    python3 versao1.py --amostras 5000 --execucoes 5
"""

import argparse
import threading
import time
from collections import Counter

N = 6                  # tamanho do buffer (3 + D2 mod 5, com D2 = 3)
TIMEOUT_S = 1.0        # 1 s sem receber nada => travamento


def executar(total: int) -> dict:
    """
    Executa uma rodada do produtor/consumidor sem sincronização.

    Parâmetros:
        total (int): quantidade de amostras que o produtor gera (0..total-1).

    Retorno:
        dict com as chaves:
            consumidas (int): leituras feitas pelo consumidor (com repetição);
            perdidas (int): amostras geradas que nunca foram consumidas;
            duplicadas (int): leituras a mais de amostras já consumidas;
            travou (bool): True se o consumidor ficou 1 s sem receber nada;
            contador_final (int): valor do contador ao fim (deveria ser 0).

    Funcionamento:
        O estado compartilhado (buffer, contador) fica num dict para que as
        duas threads enxerguem o mesmo objeto. O produtor espera enquanto
        contador == N; o consumidor espera enquanto contador == 0. Os dois
        fazem 'lido = contador; sleep(0); contador = lido +/- 1', que é a
        região crítica desprotegida.
    """
    estado = {"buffer": [None] * N, "contador": 0, "produtor_fim": False}
    recebidas = []

    def produtor() -> None:
        """Gera as amostras 0..total-1 e as coloca no buffer circular."""
        entrada = 0
        for amostra in range(total):
            while estado["contador"] >= N:      # espera ocupada: buffer cheio
                time.sleep(0)
            estado["buffer"][entrada] = amostra
            entrada = (entrada + 1) % N
            lido = estado["contador"]           # --- região crítica ---
            time.sleep(0)                       # interrupção no pior momento
            estado["contador"] = lido + 1       # --- fim da região crítica ---
        estado["produtor_fim"] = True

    def consumidor() -> bool:
        """
        Retira amostras do buffer até o produtor terminar e o contador
        esvaziar. Retorna True se travou (1 s sem receber nada).
        """
        saida = 0
        ultimo = time.monotonic()
        while True:
            if estado["contador"] > 0:
                recebidas.append(estado["buffer"][saida])
                saida = (saida + 1) % N
                lido = estado["contador"]       # --- região crítica ---
                time.sleep(0)
                estado["contador"] = lido - 1   # --- fim da região crítica ---
                ultimo = time.monotonic()
                # trava de segurança contra livelock (contador inflado)
                if len(recebidas) > 2 * total:
                    return True
            else:
                if estado["produtor_fim"] and estado["contador"] <= 0:
                    return False
                if time.monotonic() - ultimo > TIMEOUT_S:
                    return True
                time.sleep(0)

    resultado = {}
    t_prod = threading.Thread(target=produtor, daemon=True)
    t_cons = threading.Thread(
        target=lambda: resultado.__setitem__("travou", consumidor()), daemon=True)
    t_prod.start()
    t_cons.start()
    t_cons.join()

    cont = Counter(x for x in recebidas if x is not None)
    perdidas = total - len(cont)
    duplicadas = sum(c - 1 for c in cont.values() if c > 1)
    return {
        "consumidas": len(recebidas),
        "perdidas": perdidas,
        "duplicadas": duplicadas,
        "travou": resultado.get("travou", True),
        "contador_final": estado["contador"],
    }


def main() -> None:
    """Lê os argumentos, roda as execuções e imprime a tabela de resultados."""
    p = argparse.ArgumentParser(description="A4 - Versão 1 (sem sincronização)")
    p.add_argument("--amostras", type=int, default=20000)
    p.add_argument("--execucoes", type=int, default=3)
    a = p.parse_args()

    print(f"VERSÃO 1 — sem sincronização | N = {N} | {a.amostras} amostras\n")
    print(f"{'Exec':<5}{'Consumidas':>11}{'Perdidas':>10}{'Duplicadas':>12}"
          f"{'Travou':>8}{'Contador final':>16}{'Tempo (s)':>11}")
    for i in range(1, a.execucoes + 1):
        t0 = time.perf_counter()
        r = executar(a.amostras)
        dt = time.perf_counter() - t0
        print(f"{i:<5}{r['consumidas']:>11}{r['perdidas']:>10}{r['duplicadas']:>12}"
              f"{'sim' if r['travou'] else 'não':>8}{r['contador_final']:>16}{dt:>11.2f}")


if __name__ == "__main__":
    main()
