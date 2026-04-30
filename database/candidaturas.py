import json
from datetime import date
from database.connection import db_connect


def atualizar_candidatura(id_vaga: int, status: str, fase: str = None, observacao: str = None):
    with db_connect() as con:
        row = con.execute(
            "SELECT historico_fases FROM fact_vaga WHERE id = ?", [id_vaga]
        ).fetchone()
        historico = {}
        if row and row[0]:
            try:
                historico = json.loads(row[0])
            except Exception:
                historico = {}
        if status and status not in historico:
            historico[status] = str(date.today())

        con.execute(
            """
            UPDATE fact_vaga
            SET candidatura_status = ?,
                candidatura_fase = ?,
                candidatura_observacao = ?,
                candidatura_data = current_date,
                historico_fases = ?
            WHERE id = ?
        """,
            [status, fase, observacao, json.dumps(historico), id_vaga],
        )


def negar_vaga(id_vaga: int, observacao: str = None):
    with db_connect() as con:
        con.execute(
            """
            UPDATE fact_vaga
            SET negada = true,
                candidatura_status = 'negado',
                candidatura_observacao = ?,
                candidatura_data = current_date
            WHERE id = ?
        """,
            [observacao, id_vaga],
        )


def salvar_remuneracao(
    id_vaga: int,
    regime: str,
    moeda: str,
    salario_mensal: int,
    salario_anual_total: int,
    tem_vr: bool,
    valor_vr: int,
    tem_va: bool,
    valor_va: int,
    tem_vt: bool,
    valor_vt: int,
    tem_plano_saude: bool,
    tem_gympass: bool,
    tem_convenio_medico: bool,
    tem_convenio_odonto: bool,
    tem_prev_privada: bool,
    outros_beneficios: str,
    tem_sal13: bool = False,
    tem_plr: bool = False,
    valor_plr: int = 0,
    tem_bonus: bool = False,
    valor_bonus: int = 0,
):
    # Cast completo para tipos Python nativos — DuckDB rejeita numpy.*
    id_vaga = int(id_vaga)
    salario_mensal = int(salario_mensal)
    salario_anual_total = int(salario_anual_total)
    valor_vr = int(valor_vr)
    valor_va = int(valor_va)
    valor_vt = int(valor_vt)
    valor_plr = int(valor_plr)
    valor_bonus = int(valor_bonus)
    tem_vr = bool(tem_vr)
    tem_va = bool(tem_va)
    tem_vt = bool(tem_vt)
    tem_plano_saude = bool(tem_plano_saude)
    tem_gympass = bool(tem_gympass)
    tem_convenio_medico = bool(tem_convenio_medico)
    tem_convenio_odonto = bool(tem_convenio_odonto)
    tem_prev_privada = bool(tem_prev_privada)
    tem_sal13 = bool(tem_sal13)
    tem_plr = bool(tem_plr)
    tem_bonus = bool(tem_bonus)

    sal_mensal_total = (
        salario_mensal
        + (valor_vr if tem_vr else 0)
        + (valor_va if tem_va else 0)
        + (valor_vt if tem_vt else 0)
    )
    sal_anual = (
        (salario_mensal * 12)
        + (salario_mensal if tem_sal13 else 0)
        + (valor_plr if tem_plr else 0)
        + (valor_bonus if tem_bonus else 0)
    )
    with db_connect() as con:
        con.execute(
            """
            UPDATE fact_vaga SET
                regime=?, moeda=?, salario_mensal=?, salario_anual_total=?,
                tem_vr=?, valor_vr=?, tem_va=?, valor_va=?,
                tem_vt=?, valor_vt=?, tem_plano_saude=?, tem_gympass=?,
                tem_convenio_medico=?, tem_convenio_odonto=?,
                tem_prev_privada=?, outros_beneficios=?,
                tem_sal13=?, tem_plr=?, valor_plr=?,
                tem_bonus=?, valor_bonus=?,
                salario_min=?, salario_max=?
            WHERE id=?
        """,
            [
                regime,
                moeda,
                salario_mensal,
                sal_mensal_total,
                tem_vr,
                valor_vr,
                tem_va,
                valor_va,
                tem_vt,
                valor_vt,
                tem_plano_saude,
                tem_gympass,
                tem_convenio_medico,
                tem_convenio_odonto,
                tem_prev_privada,
                outros_beneficios,
                tem_sal13,
                tem_plr,
                valor_plr,
                tem_bonus,
                valor_bonus,
                sal_mensal_total,
                sal_anual,
                id_vaga,
            ],
        )
