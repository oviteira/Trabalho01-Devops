import json
import re

def is_valid_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf or '')
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10 % 11) % 10

    return cpf[-2:] == f"{d1}{d2}"

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    cpf = body.get("cpf")

    if not cpf:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "CPF é obrigatório"})
        }

    valid = is_valid_cpf(cpf)
    return {
        "statusCode": 200,
        "body": json.dumps({"valid": valid})
    }
