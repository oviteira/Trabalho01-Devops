import csv
import json
import boto3

# ==== CONFIGURAÇÕES ====
# Região onde sua Lambda está
AWS_REGION = "us-east-2"

# Nome da função Lambda
LAMBDA_FUNCTION_NAME = "valida-cpf"

# Arquivo de entrada com CPFs
INPUT_CSV = "CPFs.csv"

# Arquivo de saída com resultado
OUTPUT_CSV = "CPFs_validados.csv"
# ========================


def invocar_lambda_cpf(lambda_client, cpf: str) -> dict:
    event = {
        "body": json.dumps({"cpf": cpf})
    }

    response = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode("utf-8")
    )

    # Lê o payload retornado
    payload_bytes = response["Payload"].read()
    payload_str = payload_bytes.decode("utf-8")

    # A Lambda retorna algo tipo:
    # {
    #   "statusCode": 200,
    #   "body": "{\"valid\": true}"
    # }
    try:
        result = json.loads(payload_str)
    except json.JSONDecodeError:
        return {
            "statusCode": 500,
            "raw": payload_str,
            "valid": None,
            "error": "Resposta da Lambda não é JSON"
        }

    status_code = result.get("statusCode")
    body_str = result.get("body", "{}")

    try:
        body = json.loads(body_str)
    except json.JSONDecodeError:
        body = {}
    
    # No seu código: body é {"valid": true} ou {"error": "CPF é obrigatório"}
    valid = body.get("valid")
    error = body.get("error")

    return {
        "statusCode": status_code,
        "valid": valid,
        "error": error,
        "raw": payload_str
    }


def ler_cpfs_do_csv(caminho: str):
    """
    Retorna uma lista de dicts:
    [{"id": "01", "cpf": "59173255025"}, ...]
    """
    registros = []
    with open(caminho, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue

            if len(row) >= 2:
                id_ = row[0].strip()
                cpf = row[1].strip()
            else:
                id_ = ""
                cpf = row[0].strip()

            registros.append({"id": id_, "cpf": cpf})

    return registros

def escrever_resultado_csv(caminho: str, resultados: list):
    """
    Escreve um CSV com colunas:
    cpf, valid, statusCode, error
    """
    with open(caminho, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cpf", "valid", "statusCode", "error"])

        for r in resultados:
            writer.writerow([
                r.get("cpf"),
                r.get("valid"),
                r.get("statusCode"),
                r.get("error")
            ])


def main():
    # Cria cliente Lambda
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)

    # Lê registros (id + cpf) do arquivo
    registros = ler_cpfs_do_csv(INPUT_CSV)

    if not registros:
        print("Nenhum CPF encontrado no arquivo de entrada.")
        return

    resultados = []

    for reg in registros:
        cpf = reg["cpf"]
        id_ = reg["id"]

        print(f"Validando CPF {cpf} (linha {id_}) ...")
        result = invocar_lambda_cpf(lambda_client, cpf)

        linha_resultado = {
            "id": id_,
            "cpf": cpf,
            "valid": result.get("valid"),
            "statusCode": result.get("statusCode"),
            "error": result.get("error")
        }
        resultados.append(linha_resultado)

        # Também mostra no console
        if result.get("error"):
            print(f"  -> ERRO: {result['error']}")
        else:
            print(f"  -> valid = {result['valid']} (statusCode={result['statusCode']})")

    # Gera CSV de saída
    escrever_resultado_csv(OUTPUT_CSV, resultados)
    print(f"\nRelatório gerado em: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
