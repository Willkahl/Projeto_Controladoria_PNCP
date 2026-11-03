"""Gera docs/img/sprints.png (quadro das Sprints). Ajuste datas e status abaixo e rode:  python docs/gerar_figura_sprints.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OK, DOING, TODO = "#2E7D32", "#EF6C00", "#9E9E9E"
SPRINTS = [
    ("Sprint 0", "Repositório, planejamento e entender os dados", "14/10 a 15/10",
     ["Criar repositório e estrutura de pastas", "Ler enunciado e dicionário dos dados", "Configurar .env e requirements"], "Concluída", OK),
    ("Sprint 1", "Auditar: contar os problemas dos CSVs", "16/10",
     ["Script src/auditoria.py", "Contar máscaras, zeros, datas, nulos, encoding", "Registrar no README"], "Concluída", OK),
    ("Sprint 2", "Limpar: completar src/limpeza.py", "16/10 a 17/10",
     ["Texto, nulos e documentos", "Dinheiro e datas", "Autoteste 54/54 + pytest"], "Concluída", OK),
    ("Sprint 3", "Montar fato e 4 dimensões (regras 1 a 12)", "17/10 a 18/10",
     ["Vencedor por item, rejeitados, valores", "Comparável, economia, ciclo, perfil", "Conferir com a prova real"], "Concluída", OK),
    ("Sprint 4", "Banco: DDL do esquema estrela e carga", "18/10 a 19/10",
     ["sql/01_criar_banco.sql (PK, FK, CHECK)", "src/carregar.py em lote + validações", "Contagens e FK solta = 0"], "Concluída", OK),
    ("Sprint 5", "Perguntas de negócio em SQL", "19/10",
     ["6 perguntas em sql/02_perguntas.sql", "Comparar com a prova real"], "Concluída", OK),
    ("Sprint 6", "Power BI: 15 medidas + 6 histórias", "20/10 a 29/10",
     ["Conexão, modelo e Calendário DAX", "15 medidas em pastas", "6 páginas, menu, tooltip, conclusões"], "Concluída", OK),
    ("Sprint 7", "README, figura das Sprints e vídeo", "30/10 a 02/11",
     ["Finalizar README", "Gravar vídeo (até 7 min)", "Testar links em janela anônima e entregar"], "Concluída", OK),
]

fig, ax = plt.subplots(figsize=(16, 10.5))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(2, 96, "Planejamento em Sprints - Controladoria PNCP 2025", fontsize=20, fontweight="bold", va="center")
ax.text(2, 92.3, "Fluxo: PNCP (CSV) → Python (auditoria + limpeza) → PostgreSQL (esquema estrela) → Power BI   |   Entrega: 03/11 às 22h",
        fontsize=11, color="#555", va="center")
for x, t in [(2, "SPRINT"), (13, "OBJETIVO"), (40, "PERÍODO"), (50, "TAREFAS"), (88, "STATUS")]:
    ax.text(x, 88.5, t, fontsize=10, fontweight="bold", color="#333", va="center")
linha_h = 10.2
for i, (nome, obj, per, tarefas, status, cor) in enumerate(SPRINTS):
    y = 85 - (i + 1) * linha_h + 2
    ax.add_patch(FancyBboxPatch((1, y), 98, linha_h - 1.4, boxstyle="round,pad=0.1,rounding_size=0.8",
                                fc="#F6F8FA", ec="#D0D7DE", lw=1))
    ax.add_patch(FancyBboxPatch((1, y), 0.9, linha_h - 1.4, boxstyle="square,pad=0", fc=cor, ec=cor))
    cy = y + (linha_h - 1.4) / 2
    ax.text(2.6, cy, nome, fontsize=12, fontweight="bold", va="center")
    ax.text(13, cy, "\n".join(__import__("textwrap").wrap(obj, 30)), fontsize=10.5, va="center")
    ax.text(40, cy, per, fontsize=10.5, va="center")
    ax.text(50, cy, "\n".join("• " + t for t in tarefas), fontsize=9.8, va="center", linespacing=1.5)
    ax.add_patch(FancyBboxPatch((86.5, cy - 1.7), 11.5, 3.4, boxstyle="round,pad=0.1,rounding_size=1.2", fc=cor, ec=cor))
    ax.text(92.25, cy, status, fontsize=10, color="white", fontweight="bold", ha="center", va="center")
ax.text(2, 2.5, "Cada Sprint termina com algo conferível na prova real (anexo 8 do enunciado).", fontsize=10, color="#555")
Path(__file__).parent.joinpath("img").mkdir(exist_ok=True)
fig.savefig(Path(__file__).parent / "img" / "sprints.png", dpi=110, bbox_inches="tight", facecolor="white")
