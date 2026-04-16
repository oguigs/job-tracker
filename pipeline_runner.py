import time
import duckdb
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich import print as rprint

console = Console()

DB_PATH = "data/curated/jobs.duckdb"

def log_etapa(nome: str, status: str, duracao: float = None, detalhe: str = ""):
    icon = {
        "iniciando": "[yellow]⟳[/yellow]",
        "ok": "[green]✓[/green]",
        "erro": "[red]✗[/red]",
        "aviso": "[yellow]⚠[/yellow]"
    }.get(status, "•")

    duracao_str = f"[dim]{duracao:.1f}s[/dim]" if duracao else ""
    detalhe_str = f"[dim] — {detalhe}[/dim]" if detalhe else ""
    console.print(f"  {icon} {nome} {duracao_str}{detalhe_str}")

def buscar_empresas():
    con = duckdb.connect(DB_PATH)
    empresas = con.execute("""
        SELECT nome, url_vagas FROM dim_empresa
        WHERE ativa = true AND url_vagas IS NOT NULL
    """).fetchall()
    con.close()
    return empresas

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
    total_encerradas = 0

    for nome, url_vagas in empresas:
        console.print(f"[bold cyan]► {nome}[/bold cyan]")
        inicio_empresa = time.time()

        try:
            # ETAPA 1 — Coleta
            t = time.time()
            log_etapa("Coletando vagas", "iniciando")
            from scrapers.gupy_scraper import buscar_vagas
            vagas = buscar_vagas(url_vagas)
            log_etapa("Coleta", "ok", time.time() - t, f"{len(vagas)} vagas encontradas")

            # ETAPA 2 — Descrições
            t = time.time()
            log_etapa("Coletando descrições", "iniciando")
            from playwright.sync_api import sync_playwright
            vagas_enriquecidas = []
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                with Progress(
                    SpinnerColumn(),
                    TextColumn("  [dim]{task.description}[/dim]"),
                    BarColumn(bar_width=30),
                    TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Descrições", total=len(vagas))
                    for vaga in vagas:
                        try:
                            page.goto(vaga["link"], wait_until="networkidle")
                            page.wait_for_selector(
                                "[class*='description'], [class*='jobDescription'], section",
                                timeout=10000
                            )
                            el = page.query_selector(
                                "[class*='description'], [class*='jobDescription'], section"
                            )
                            vaga["descricao"] = el.inner_text().strip() if el else ""
                        except:
                            vaga["descricao"] = ""
                        vagas_enriquecidas.append(vaga)
                        progress.advance(task)
                browser.close()
            log_etapa("Descrições", "ok", time.time() - t, f"{len(vagas_enriquecidas)} processadas")

            # ETAPA 3 — Extração de stacks
            t = time.time()
            log_etapa("Extraindo stacks", "iniciando")
            from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
            from database.db_manager import upsert_empresa, inserir_vaga, gerar_hash, verificar_vagas_encerradas, registrar_log
            import duckdb as ddb

            id_empresa = upsert_empresa(nome=nome, url_vagas=url_vagas)
            vagas_novas = 0

            for vaga in vagas_enriquecidas:
                descricao = vaga.get("descricao", "")
                titulo = vaga.get("titulo", "")
                vaga["stacks"] = extrair_stacks(descricao)
                vaga["nivel"] = detectar_nivel(titulo)
                vaga["modalidade"] = detectar_modalidade(
                    descricao,
                    modalidade_coletada=vaga.get("modalidade", "não identificado")
                )

                con_check = ddb.connect(DB_PATH)
                negada = con_check.execute(
                    "SELECT id FROM fact_vaga WHERE hash = ? AND negada = true",
                    [gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])]
                ).fetchone()
                con_check.close()

                if negada:
                    continue

                inserida = inserir_vaga(vaga, id_empresa)
                if inserida:
                    vagas_novas += 1

            log_etapa("Stacks", "ok", time.time() - t, f"{vagas_novas} vagas novas")

            # ETAPA 4 — Vagas encerradas
            t = time.time()
            links_ativos = [v["link"] for v in vagas_enriquecidas]
            encerradas = verificar_vagas_encerradas(id_empresa, links_ativos)
            if encerradas:
                log_etapa("Vagas encerradas", "aviso", time.time() - t, f"{len(encerradas)} encerradas")
                for titulo in encerradas:
                    console.print(f"    [dim]- {titulo[:60]}[/dim]")
            else:
                log_etapa("Vagas encerradas", "ok", time.time() - t, "nenhuma encerrada")

            duracao_total = time.time() - inicio_empresa
            registrar_log(nome, len(vagas), vagas_novas, "sucesso")

            total_encontradas += len(vagas)
            total_novas += vagas_novas
            total_encerradas += len(encerradas)

            console.print(f"  [dim]Tempo total: {duracao_total:.1f}s[/dim]\n")

        except Exception as e:
            duracao_total = time.time() - inicio_empresa
            log_etapa("Erro", "erro", duracao_total, str(e)[:80])
            registrar_log(nome, 0, 0, "erro", str(e))
            console.print()

    # RESUMO FINAL
    table = Table(title="Resumo do pipeline", border_style="cyan", show_header=True)
    table.add_column("Métrica", style="bold")
    table.add_column("Valor", justify="right")

    table.add_row("Empresas processadas", str(len(empresas)))
    table.add_row("Vagas encontradas", str(total_encontradas))
    table.add_row("Vagas novas", f"[green]{total_novas}[/green]")
    table.add_row("Vagas encerradas", f"[yellow]{total_encerradas}[/yellow]" if total_encerradas else "0")

    console.print(table)
    console.print(f"\n[dim]Pipeline concluído em {datetime.now().strftime('%H:%M:%S')}[/dim]\n")


if __name__ == "__main__":
    rodar_pipeline_visual()