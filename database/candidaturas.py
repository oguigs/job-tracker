from database.connection import db_connect


def atualizar_candidatura(id_vaga: int, status: str,
                          fase: str = None, observacao: str = None):
    with db_connect() as con:
        con.execute("""
            UPDATE fact_vaga
            SET candidatura_status = ?,
                candidatura_fase = ?,
                candidatura_observacao = ?,
                candidatura_data = current_date
            WHERE id = ?
        """, [status, fase, observacao, id_vaga])


def negar_vaga(id_vaga: int, observacao: str = None):
    with db_connect() as con:
        con.execute("""
            UPDATE fact_vaga
            SET negada = true,
                candidatura_status = 'negado',
                candidatura_fase = candidatura_status,
                candidatura_observacao = ?,
                candidatura_data = current_date
            WHERE id = ?
        """, [observacao, id_vaga])


def salvar_remuneracao(id_vaga: int, regime: str, moeda: str,
                       salario_mensal: int, salario_anual_total: int,
                       tem_vr: bool, valor_vr: int,
                       tem_va: bool, valor_va: int,
                       tem_vt: bool, valor_vt: int,
                       tem_plano_saude: bool, tem_gympass: bool,
                       tem_convenio_medico: bool, tem_convenio_odonto: bool,
                       tem_prev_privada: bool, outros_beneficios: str):
    with db_connect() as con:
        con.execute("""
            UPDATE fact_vaga SET
                regime=?, moeda=?, salario_mensal=?, salario_anual_total=?,
                tem_vr=?, valor_vr=?, tem_va=?, valor_va=?,
                tem_vt=?, valor_vt=?, tem_plano_saude=?, tem_gympass=?,
                tem_convenio_medico=?, tem_convenio_odonto=?,
                tem_prev_privada=?, outros_beneficios=?
            WHERE id=?
        """, [regime, moeda, salario_mensal, salario_anual_total,
              tem_vr, valor_vr, tem_va, valor_va, tem_vt, valor_vt,
              tem_plano_saude, tem_gympass, tem_convenio_medico,
              tem_convenio_odonto, tem_prev_privada, outros_beneficios,
              id_vaga])
