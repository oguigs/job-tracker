from database.connection import conectar

def atualizar_candidatura(id_vaga: int, status: str,
                           fase: str = None, observacao: str = None):
    con = conectar()
    con.execute("""
        UPDATE fact_vaga
        SET candidatura_status = ?,
            candidatura_fase = ?,
            candidatura_observacao = ?,
            candidatura_data = current_date
        WHERE id = ?
    """, [status, fase, observacao, id_vaga])
    con.close()

def negar_vaga(id_vaga: int, observacao: str = None):
    con = conectar()
    con.execute("""
        UPDATE fact_vaga
        SET negada = true,
            candidatura_status = 'negado',
            candidatura_fase = candidatura_status,
            candidatura_observacao = ?,
            candidatura_data = current_date
        WHERE id = ?
    """, [observacao, id_vaga])
    con.close()

def salvar_remuneracao(id_vaga: int, regime: str, moeda: str,
                        salario_min: int, salario_max: int, salario_anual: bool,
                        tem_vr: bool, valor_vr: int,
                        tem_va: bool, valor_va: int,
                        tem_vt: bool, valor_vt: int,
                        outros_beneficios: str):
    con = conectar()
    con.execute("""
        UPDATE fact_vaga SET
            regime=?, moeda=?, salario_min=?, salario_max=?, salario_anual=?,
            tem_vr=?, valor_vr=?, tem_va=?, valor_va=?,
            tem_vt=?, valor_vt=?, outros_beneficios=?
        WHERE id=?
    """, [regime, moeda, salario_min, salario_max, salario_anual,
          tem_vr, valor_vr, tem_va, valor_va,
          tem_vt, valor_vt, outros_beneficios, id_vaga])
    con.close()    