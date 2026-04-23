import great_expectations as gx
import pandas as pd
from database.connection import db_connect


def validar_vagas() -> dict:
    """Valida qualidade dos dados da fact_vaga."""
    with db_connect(read_only=True) as con:
        df = con.execute("SELECT * FROM fact_vaga").df()

    context = gx.get_context()
    ds = context.sources.add_pandas("vagas_ds")
    da = ds.add_dataframe_asset("vagas")
    batch = da.build_batch_request(dataframe=df)

    suite = context.add_or_update_expectation_suite("vagas_suite")
    validator = context.get_validator(batch_request=batch, expectation_suite=suite)

    validator.expect_column_values_to_not_be_null("id")
    validator.expect_column_values_to_not_be_null("titulo")
    validator.expect_column_values_to_not_be_null("id_empresa")
    validator.expect_column_values_to_be_in_set("candidatura_status", [
        "nao_inscrito", "inscrito", "chamado", "recrutador",
        "fase_1", "fase_2", "fase_3", "aprovado", "reprovado", "negado"
    ])
    validator.expect_column_values_to_not_be_null("link")
    validator.expect_column_values_to_be_unique("hash")

    results = validator.validate()
    return {
        "success": results["success"],
        "total": results["statistics"]["evaluated_expectations"],
        "passed": results["statistics"]["successful_expectations"],
        "failed": results["statistics"]["unsuccessful_expectations"],
        "results": results["results"]
    }
