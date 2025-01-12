"""
Testes relacionados aos status de participantes
"""
import itertools

from httpx import Client

from fastapi import status

import pytest


@pytest.fixture()
def input_part() -> dict:
    """Template de Status dos Participantes

    Returns:
        dict: template de exemplo
    """
    return {
        "participante_ativo": True,
        "matricula_siape": 123456,
        "cpf_participante": 99160773120,
        "modalidade_execucao": 3,
        "jornada_trabalho_semanal": 40,
    }


fields_participantes = (
    ["participante_ativo_inativo_pgd"],
    ["matricula_siape"],
    ["cpf_participante"],
    ["modalidade_execucao"],
    ["jornada_trabalho_semanal"],
)


def test_put_participante(
    input_part: dict, header_usr_1: dict, truncate_part, client: Client
):
    """Testa a submissão de um participante a partir do template"""
    response = client.put("/participante/123456", json=input_part, headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_part


def test_put_duplicate_participante(
    input_part: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    truncate_part,
    client: Client,
):
    """Testa a submissão de um participante duplicado
    TODO: Verificar regra negocial"""
    response = client.put("/participante/123456", json=input_part, headers=header_usr_1)
    response = client.put("/participante/123456", json=input_part, headers=header_usr_2)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_part


@pytest.mark.parametrize("missing_fields", enumerate(fields_participantes))
def test_put_participante_missing_mandatory_fields(
    input_part: dict,
    missing_fields: list,
    header_usr_1: dict,
    truncate_part,
    client: Client,
):
    """Tenta submeter participantes faltando campos obrigatórios"""
    offset, field_list = missing_fields
    for field in field_list:
        del input_part[field]

    input_part["matricula_siape"] = 1800 + offset  # precisa ser um novo participante
    response = client.put(
        f"/participante/{input_part['cod_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_participante(
    header_usr_1: dict, truncate_part, example_part, client: Client
):
    """Tenta requisitar um participante pelo cod_siape
    TODO: Verificar regra negocial"""
    response = client.get("/participante/123456", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK


def test_get_participante_inexistente(header_usr_1: dict, client: Client):
    response = client.get("/participante/888888888", headers=header_usr_1)

    assert response.status_code == 404
    assert response.json().get("detail", None) == "Participante não encontrado"


@pytest.mark.parametrize(
    "matricula_siape",
    [
        ("12345678"),
        ("0000000"),
        ("9999999"),
        ("123456"),
        (""),
    ],
)
def test_put_participante_invalid_matricula_siape(
    input_part: dict,
    matricula_siape: str,
    header_usr_1: dict,
    truncate_part,
    client: Client,
):
    """Tenta submeter um participante com matricula siape inválida"""

    input_part["matricula_siape"] = matricula_siape

    response = client.put(
        f"/participante/{input_part['cod_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = [
        "Matricula SIAPE Inválida.",
        "Matrícula SIAPE deve ter 7 digitos.",
    ]
    assert response.json().get("detail")[0]["msg"] in detail_msg


@pytest.mark.parametrize(
    "cpf",
    [
        ("11111111111"),
        ("22222222222"),
        ("33333333333"),
        ("44444444444"),
        ("04811556435"),
        ("444-444-444.44"),
        ("-44444444444"),
        ("444444444"),
        ("-444 4444444"),
        ("4811556437"),
        ("048115564-37"),
        ("04811556437     "),
        ("    04811556437     "),
        (""),
    ],
)
def test_put_participante_invalid_cpf(
    input_part: dict, cpf: str, header_usr_1: dict, truncate_part, client: Client
):
    """Tenta submeter um participante com cpf inválido"""
    input_part["cpf"] = cpf

    response = client.put(
        f"/participante/{input_part['cod_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = [
        "Digitos verificadores do CPF inválidos.",
        "CPF inválido.",
        "CPF precisa ter 11 digitos.",
        "CPF deve conter apenas digitos.",
    ]
    assert response.json().get("detail")[0]["msg"] in detail_msg


@pytest.mark.parametrize(
    "participante_ativo_inativo_pgd",
    [
        (3),
        (-1),
    ],
)
def test_put_part_invalid_participante_ativo_inativo_pgd(
    input_part: dict,
    participante_ativo_inativo_pgd: int,
    header_usr_1: dict,
    truncate_part,
    client: Client,
):
    """Tenta submeter um participante com flag ativo_inativo_pgd inválida"""
    input_part[
        "invalid_participante_ativo_inativo_pgd"
    ] = participante_ativo_inativo_pgd
    response = client.put(
        f"/participante/{input_part['cod_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Boolean participante_ativo_inativo_pgd inválida; permitido: 0, 1"
    # detail_msg = "value is not a valid enumeration member; permitted: 0,1"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize("modalidade_execucao", [(0), (-1), (5)])
def test_put_part_invalid_modalidade_execucao(
    input_part: dict,
    modalidade_execucao: int,
    header_usr_1: dict,
    truncate_part,
    client: Client,
):
    """Tenta submeter um participante com modalidade de execução inválida"""
    input_part["modalidade_execucao"] = modalidade_execucao
    response = client.put(
        f"/participante/{input_part['cod_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Modalidade de execução inválida; permitido: 1, 2, 3, 4"
    # detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3, 4"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize(
    "jornada_trabalho_semanal",
    [
        (45),
        (-2),
        (0),
    ],
)
def test_put_part_invalid_jornada_trabalho_semanal(
    input_part: dict,
    jornada_trabalho_semanal: int,
    header_usr_1: dict,
    truncate_part,
    client: Client,
):
    """Tenta submeter um participante com jornada de trabalho semanal inválida"""
    input_part["jornada_trabalho_semanal"] = jornada_trabalho_semanal
    response = client.put(
        f"/participante/{input_part['cod_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Carga horária semanal deve ser entre 1 e 40"
    assert response.json().get("detail")[0]["msg"] == detail_msg
