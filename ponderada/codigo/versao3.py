"""
versao3.py — Ponderada CC08 (Tato), questão A4, Versão 3: ORDEM TROCADA.

Autora: Anne Esther Lins Figueirôa  (D1 = 4, D2 = 3, N = 6)

Igual à versão 2, exceto que o PRODUTOR faz wait(mutex) ANTES de wait(vazio).
Quando o buffer enche, o produtor dorme em 'vazio' segurando o mutex; o
consumidor, para liberar uma posição, precisa do mutex e dorme também.
Espera circular entre duas threads => deadlock.

Como semáforos não têm dono, o travamento é detectado por timeout: se o
consumidor fica 1 s sem conseguir o mutex/uma amostra, a execução é
registrada como travada.

Uso:
    python3 versao3.py
    python3 versao3.py --amostras 5000 --execucoes 5
"""

import argparse
import threading
import time
from collections import Counter

N = 6
TIMEOUT_S = 1.0


def executar(total: int) -> dict:
    """
    Executa uma rodada do produtor/consumidor com a ordem de wait trocada.

    Parâmetros:
        total (int): quantidade de amostras geradas (0..total-1).

    Retorno:
        dict com consumidas, perdidas, duplicadas, travou, e 'onde':
        descrição de em qual semáforo cada thread estava bloqueada.

    Funcionamento:
        Produtor: wait(mutex) -> wait(vazio) -> insere -> signal(mutex) -> signal(cheio)
        Consumidor: wait(cheio) -> wait(mutex) -> retira -> signal(mutex) -> signal(vazio)
    """
    buffer = [None] * N
    vazio = threading.Semaphore(N)
    cheio = threading.Semaphore(0)
    mutex = threading.Semaphore(1)
    recebidas = []
    onde = {"produtor": "terminou", "consumidor": "terminou"}
    idx = {"entrada": 0, "saida": 0}

    def produtor() -> None:
        """Produz com a ordem errada: pega o mutex antes de ver se há espaço."""
        for amostra in range(total):
            if not mutex.acquire(timeout=TIMEOUT_S):          # wait(mutex)
                onde["produtor"] = f"esperando mutex (amostra {amostra})"; return
            if not vazio.acquire(timeout=TIMEOUT_S):          # wait(vazio) — segurando mutex!
                onde["produtor"] = f"segurando mutex, esperando vazio (amostra {amostra})"
                return                                        # sai sem liberar: simula thread congelada
            buffer[idx["entrada"]] = amostra
            idx["entrada"] = (idx["entrada"] + 1) % N
            time.sleep(0)
            mutex.release()
            cheio.release()

    def consumidor() -> None:
        """Consome normalmente; fica preso no mutex quando o produtor o segura."""
        for _ in range(total):
            if not cheio.acquire(timeout=TIMEOUT_S):          # wait(cheio)
                onde["consumidor"] = "esperando cheio"; return
            if not mutex.acquire(timeout=TIMEOUT_S):          # wait(mutex)
                onde["consumidor"] = "esperando mutex (buffer cheio)"; return
            recebidas.append(buffer[idx["saida"]])
            idx["saida"] = (idx["saida"] + 1) % N
            time.sleep(0)
            mutex.release()
            vazio.release()

    tp = threading.Thread(target=produtor, daemon=True)
    tc = threading.Thread(target=consumidor, daemon=True)
    tp.start(); tc.start()
    tc.join(); tp.join()

    cont = Counter(recebidas)
    travou = len(recebidas) < total
    return {
        "consumidas": len(recebidas),
        "perdidas": total - len(cont),
        "duplicadas": sum(c - 1 for c in cont.values() if c > 1),
        "travou": travou,
        "onde": onde,
    }


def main() -> None:
    """Lê os argumentos, roda as execuções e imprime a tabela e o diagnóstico."""
    p = argparse.ArgumentParser(description="A4 - Versão 3 (ordem trocada)")
    p.add_argument("--amostras", type=int, default=20000)
    p.add_argument("--execucoes", type=int, default=3)
    a = p.parse_args()

    print(f"VERSÃO 3 — produtor faz wait(mutex) antes de wait(vazio) | N = {N} | "
          f"{a.amostras} amostras\n")
    print(f"{'Exec':<5}{'Consumidas':>11}{'Perdidas':>10}{'Duplicadas':>12}"
          f"{'Travou':>8}{'Tempo (s)':>11}")
    diagnosticos = []
    for i in range(1, a.execucoes + 1):
        t0 = time.perf_counter()
        r = executar(a.amostras)
        dt = time.perf_counter() - t0
        print(f"{i:<5}{r['consumidas']:>11}{r['perdidas']:>10}{r['duplicadas']:>12}"
              f"{'sim' if r['travou'] else 'não':>8}{dt:>11.2f}")
        diagnosticos.append(r["onde"])
    print("\nOnde cada thread parou:")
    for i, d in enumerate(diagnosticos, 1):
        print(f"  exec {i}: produtor -> {d['produtor']}; consumidor -> {d['consumidor']}")


if __name__ == "__main__":
    main()
