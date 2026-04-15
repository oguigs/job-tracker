import great_expectations as gx
from database.connection import conectar
import pandas as pd

def validar_vagas() -> dict:
    """Valida qualidade dos dados da fact_vaga."""
    con = conectar()
    df = con.execute("SELECT * FROM fact_vaga").df()
    con.close()

    context = gx.get_context()
    ds = context.sources.add_pandas("vagas_ds")
    da = ds.add_dataframe_asset("vagas")
    batch = da.build_batch_request(dataframe=df)

    suite = context.add_expectation_suite("vagas_suite")

    validator = context.get_validator(
        batch_request=batch,
        expectation_suite=suite
    )

    # expectativas
    validator.expect_column_values_to_not_be_null("titulo")
    validator.expect_column_values_to_not_be_null("id_empresa")
    validator.expect_column_values_to_not_be_null("hash")
    validator.expect_column_values_to_be_unique("hash")
    validator.expect_column_values_to_be_in_set("nivel", [
        "junior", "pleno", "senior", "especialista",
        "não identificado", "lead"
    ])
    validator.expect_column_values_to_be_in_set("modalidade", [
        "remoto", "hibrido", "presencial", "não identificado"
    ])

    results = validator.validate()

    resumo = {
        "success": results["success"],
        "total": results["statistics"]["evaluated_expectations"],
        "passed": results["statistics"]["successful_expectations"],
        "failed": results["statistics"]["unsuccessful_expectations"],
        "detalhes": []
    }

    for r in results["results"]:
        if not r["success"]:
            resumo["detalhes"].append({
                "coluna": r["expectation_config"]["kwargs"].get("column"),
                "expectativa": r["expectation_config"]["expectation_type"],
                "resultado": r["result"]
            })

    return resumo

if __name__ == "__main__":
    resultado = validar_vagas()
    print(f"\nQualidade dos dados:")
    print(f"  Status: {'✅ OK' if resultado['success'] else '⚠️ Falhas encontradas'}")
    print(f"  Passed: {resultado['passed']}/{resultado['total']}")
    if resultado["detalhes"]:
        print(f"\nFalhas:")
        for d in resultado["detalhes"]:
            print(f"  - {d['coluna']}: {d['expectativa']}")