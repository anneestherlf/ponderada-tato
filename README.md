# Ponderada CC08 — Tato: do pipeline ao deadlock

**Anne Esther Lins Figueirôa**

Análise de arquitetura, pipeline, processos, semáforos e deadlock de uma pulseira sensorial para pessoas com deficiência visual, com a decisão de CTO em [`ponderada/ponderada-tato.md`](ponderada/ponderada-tato.md).

## Estrutura

```
.
├── README.md
├── .gitignore
└── ponderada/
    ├── ponderada-tato.md   # Parte A (técnica) e Parte B (memorando do CTO)
    ├── codigo/             # questão A4: produtor/consumidor
    │   ├── versao1.py      # sem sincronização (condição de corrida)
    │   ├── versao2.py      # semáforos vazio / cheio / mutex
    │   └── versao3.py      # ordem dos wait trocada (deadlock)
    └── img/                # prints
```

## Como rodar a A4

Requisito: Python 3.8+ (só biblioteca padrão, nada para instalar).

```bash
cd ponderada/codigo

python3 versao1.py   # Versão 1: sem sincronização
python3 versao2.py   # Versão 2: com semáforos
python3 versao3.py   # Versão 3: ordem trocada (deadlock)
```

Cada comando executa **3 rodadas de 20.000 amostras** com buffer de **N = 6** e imprime uma tabela com amostras consumidas, perdidas, duplicadas e se travou. Opcionalmente:

```bash
python3 versao1.py --amostras 5000 --execucoes 5
```

A versão 3 encerra sozinha após detectar o travamento (1 s sem progresso).
