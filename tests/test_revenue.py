from pathlib import Path
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import app as provider
import runtime

client = TestClient(provider.app)
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def offline(monkeypatch):
    # Exercise a real refused database connection without disturbing the test database.
    isolated = create_engine("postgresql+psycopg://127.0.0.1:1/postgres", connect_args={"connect_timeout": 1})
    monkeypatch.setattr(provider, "engine", isolated)
    monkeypatch.setattr(runtime, "engine", isolated)
    yield
    isolated.dispose()


def test_health():
    assert client.get("/health").json()["status"] == "ready"

from lxml import etree as xml
from zeep import Client

folder = ROOT/"contracts/v1"
binding = Client(str(folder/"revenue.wsdl"))
auth = (os.environ["REVENUE_USER"], os.environ["REVENUE_PASSWORD"])


def call(student="MHSTU0001", kind="INCOME", credentials=auth, raw=None):
    if raw is None:
        node = binding.create_message(binding.service, "GetStudentCertificates", StudentID=student,
                                      CertificateType=kind, RequestReference="test-request")
        raw = xml.tostring(node)
    return client.post("/soap/v1", content=raw, headers={"Content-Type": "application/soap+xml"}, auth=credentials)


@pytest.mark.parametrize("student,kind,field,value", [
    ("MHSTU0001", "INCOME", "AnnualIncomeINR", "150000.00"),
    ("MHSTU0001", "CASTE", "Category", "DEMO-A"),
    ("MHSTU0003", "INCOME", "CertificateStatus", "EXPIRED"),
])
def test_lookup(student, kind, field, value):
    response = call(student, kind)
    assert response.status_code == 200
    assert "application/soap+xml" in response.headers["content-type"]
    result = xml.fromstring(response.content).find(provider.S+"Body")[0]
    provider.SCHEMA.assertValid(result)
    assert result.findtext(".//"+provider.R+field) == value


@pytest.mark.parametrize("kwargs,status,code", [
    ({"student": "MHSTU9999"}, 404, "RECORD_MISSING"),
    ({"credentials": ("bad","bad")}, 401, "INVALID_CREDENTIALS"),
    ({"raw": b"<broken"}, 400, "INVALID_XML"),
    ({"raw": b"<invalid/>"}, 400, "INVALID_ENVELOPE"),
    ({"raw": b'<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><other/></s:Body></s:Envelope>'},
     400, "UNSUPPORTED_OPERATION"),
])
def test_fault(kwargs, status, code):
    response = call(**kwargs)
    assert response.status_code == status
    fault_detail = xml.fromstring(response.content).find(".//"+provider.R+"ProviderFault")
    provider.SCHEMA.assertValid(fault_detail)
    assert fault_detail.findtext(provider.R+"Code") == code


def test_database_failure(offline):
    response = call()
    assert response.status_code == 503
    assert b"DATABASE_UNAVAILABLE" in response.content
    assert client.get("/health").status_code == 503
