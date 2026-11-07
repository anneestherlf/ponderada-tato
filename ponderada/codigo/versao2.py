"""
versao2.py - Ponderada CC08 (Tato), questão A4, Versão 2: COM semáforos.

Autora: Anne Esther Lins Figueirôa  (D1 = 4, D2 = 3, N = 6)

Solução clássica do produtor/consumidor com buffer limitado (Dijkstra):
    vazio = N  -> conta posições livres; bloqueia o produtor com buffer cheio
    cheio = 0  -> conta posições ocupadas; bloqueia o consumidor com buffer vazio
    mutex = 1  -> exclusão mútua no acesso ao buffer e aos índices

Ordem correta no produtor:  wait(vazio) -> wait(mutex) -> insere -> signal(mutex) -> signal(cheio)
Ordem correta no consumidor: wait(cheio) -> wait(mutex) -> retira -> signal(mutex) -> signal(vazio)

O mesmo time.sleep(0) da versão 1 continua dentro da região crítica: agora
a interrupção acontece, mas não causa dano, porque ninguém mais entra nela.

Uso:
    python3 versao2.py
    python3 versao2.py --amostras 5000 --execucoes 5
"""

import argparse
import threading
import time
from collections import Counter

N = 6
TIMEOUT_S = 1.0


def executar(total: int) -> dict:
    """
    Executa uma rodada do produtor/consumidor sincronizado com semáforos.

    Parâmetros:
        total (int): quantidade de amostras geradas (0..total-1).

    Retorno:
        dict com consumidas, perdidas, duplicadas, travou e
        ocupadas_final (posições ocupadas ao final; deveria ser 0).

    Funcionamento:
        Cada wait() usa acquire(timeout=1 s); se algum estourar, a execução
        é registrada como travamento (não deve acontecer nesta versão).
    """
    buffer = [None] * N
    vazio = threading.Semaphore(N)
    cheio = threading.Semaphore(0)
    mutex = threading.Semaphore(1)
    recebidas = []
    travou = threading.Event()
    idx = {"entrada": 0, "saida": 0, "ocupadas": 0}

    def produtor() -> None:
        """Gera amostras e as insere no buffer respeitando os semáforos."""
        for amostra in range(total):
            if not vazio.acquire(timeout=TIMEOUT_S):   # wait(vazio)
                travou.set(); return
            if not mutex.acquire(timeout=TIMEOUT_S):   # wait(mutex)
                travou.set(); return
            buffer[idx["entrada"]] = amostra            # --- região crítica ---
            idx["entrada"] = (idx["entrada"] + 1) % N
            lido = idx["ocupadas"]
            time.sleep(0)
            idx["ocupadas"] = lido + 1                  # --- fim ---
            mutex.release()                             # signal(mutex)
            cheio.release()                             # signal(cheio)

    def consumidor() -> None:
        """Retira exatamente 'total' amostras; marca travamento após 1 s parado."""
        for _ in range(total):
            if not cheio.acquire(timeout=TIMEOUT_S):   # wait(cheio)
                travou.set(); return
            if not mutex.acquire(timeout=TIMEOUT_S):   # wait(mutex)
                travou.set(); return
            recebidas.append(buffer[idx["saida"]])      # --- região crítica ---
            idx["saida"] = (idx["saida"] + 1) % N
            lido = idx["ocupadas"]
            time.sleep(0)
            idx["ocupadas"] = lido - 1                  # --- fim ---
            mutex.release()                             # signal(mutex)
            vazio.release()                             # signal(vazio)

    tp = threading.Thread(target=produtor, daemon=True)
    tc = threading.Thread(target=consumidor, daemon=True)
    tp.start(); tc.start()
    tc.join(); tp.join(timeout=TIMEOUT_S)

    cont = Counter(recebidas)
    return {
        "consumidas": len(recebidas),
        "perdidas": total - len(cont),
        "duplicadas": sum(c - 1 for c in cont.values() if c > 1),
        "travou": travou.is_set(),
        "ocupadas_final": idx["ocupadas"],
        "em_ordem": recebidas == list(range(len(recebidas))),
    }


def main() -> None:
    """Lê os argumentos, roda as execuções e imprime a tabela de resultados."""
    p = argparse.ArgumentParser(description="A4 - Versão 2 (semáforos)")
    p.add_argument("--amostras", type=int, default=20000)
    p.add_argument("--execucoes", type=int, default=3)
    a = p.parse_args()

    print(f"VERSÃO 2 - semáforos vazio/cheio/mutex | N = {N} | {a.amostras} amostras\n")
    print(f"{'Exec':<5}{'Consumidas':>11}{'Perdidas':>10}{'Duplicadas':>12}"
          f"{'Travou':>8}{'Ocupadas final':>16}{'Em ordem':>10}{'Tempo (s)':>11}")
    for i in range(1, a.execucoes + 1):
        t0 = time.perf_counter()
        r = executar(a.amostras)
        dt = time.perf_counter() - t0
        print(f"{i:<5}{r['consumidas']:>11}{r['perdidas']:>10}{r['duplicadas']:>12}"
              f"{'sim' if r['travou'] else 'não':>8}{r['ocupadas_final']:>16}"
              f"{'sim' if r['em_ordem'] else 'não':>10}{dt:>11.2f}")


if __name__ == "__main__":
    main()
