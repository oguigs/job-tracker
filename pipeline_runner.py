"""
pipeline_runner.py — Entrypoint com visualização rica usando Rich.
Chama a mesma lógica de main.py com output formatado.
"""
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from database.connection import db_connect
from database.logs import ultima_execucao_sucesso
from main import (
    processar_empresa,
    processar_empresa_greenhouse,
    processar_empresa_inhire,
    processar_empresa_smartrecruiters,
    processar_empresa_amazon,
    processar_empresa_bcg,
    titulo_relevante,
    localidade_relevante,
)

console = Console()


def log_etapa(nome: str, status: str, duracao: float = None, detalhe: str = ""):
    icon = {
        "iniciando": "[yellow]⟳[/yellow]",
        "ok":        "[green]✓[/green]",
        "erro":      "[red]✗[/red]",
        "aviso":     "[yellow]⚠[/yellow]",
        "pulado":    "[dim]⏭[/dim]",
    }.get(status, "•")
    duracao_str = f"[dim]{duracao:.1f}s[/dim]" if duracao else ""
    detalhe_str = f"[dim] — {detalhe}[/dim]" if detalhe else ""
    console.print(f"  {icon} {nome} {duracao_str}{detalhe_str}")


def buscar_empresas() -> list:
    with db_connect() as con:
        return con.execute("""
            SELECT nome, url_vagas FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL
        """).fetchall()


def rodar_pipeline_visual():
    console.print(Panel.fit(
        f"[bold cyan]Job Tracker — Pipeline[/bold cyan]\n"
        f"[dim]{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/dim]",
        border_style="cyan"
    ))

    empresas = buscar_empresas()
    if not empresas:
        console.print("[yellow]Nenhuma empresa ativa no banco.[/yellow]")
        return

    console.print(f"\n[bold]Empresas monitoradas:[/bold] {len(empresas)}\n")

    resumo = []
    total_encontradas = 0
    total_novas = 0

    for nome, url_vagas in empresas:
        console.print(f"[bold cyan]► {nome}[/bold cyan]")
        inicio = time.time()
        horas = ultima_execucao_sucesso(nome)

        if horas < 12:
            log_etapa(nome, "pulado", detalhe=f"última execução há {horas}h")
            resumo.append((nome, 0, 0, "pulado"))
            continue

        try:
            url = url_vagas or ""
            if "greenhouse.io" in url:
                slug = url.split("greenhouse.io/")[-1].split("/")[0]
                encontradas, novas, erro = processar_empresa_greenhouse(nome, slug)
            elif "inhire.app" in url:
                encontradas, novas, erro = processar_empresa_inhire(nome, url)
            elif "smartrecruiters.com" in url:
                encontradas, novas, erro = processar_empresa_smartrecruiters(nome, url)
            elif "amazon.jobs" in url:
                encontradas, novas, erro = processar_empresa_amazon(nome)
            elif "bcg.com" in url or "careers.bcg" in url:
                encontradas, novas, erro = processar_empresa_bcg(nome, url)
            else:
                encontradas, novas, erro = processar_empresa(nome, url)

            duracao = time.time() - inicio
            if erro and "cooldown" not in erro and "bloqueado" not in erro:
                log_etapa(nome, "erro", duracao, erro[:60])
                resumo.append((nome, 0, 0, "erro"))
            else:
                total_encontradas += encontradas
                total_novas += novas
                log_etapa(nome, "ok", duracao, f"{encontradas} vagas | {novas} novas")
                resumo.append((nome, encontradas, novas, "ok"))

        except Exception as e:
            log_etapa(nome, "erro", detalhe=str(e)[:60])
            resumo.append((nome, 0, 0, "erro"))

    # tabela resumo
    console.print("\n")
    table = Table(title="Resumo do pipeline", border_style="cyan")
    table.add_column("Empresa", style="bold")
    table.add_column("Encontradas", justify="right")
    table.add_column("Novas", justify="right", style="green")
    table.add_column("Status")
    for nome, enc, nov, status in resumo:
        cor = "green" if status == "ok" else "red" if status == "erro" else "dim"
        table.add_row(nome, str(enc), str(nov), f"[{cor}]{status}[/{cor}]")
    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {total_encontradas} encontradas | [green]{total_novas} novas[/green]")


if __name__ == "__main__":
    rodar_pipeline_visual()
