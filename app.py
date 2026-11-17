"""Contract-first SOAP 1.2 document/literal service."""
from datetime import UTC, datetime
from email.message import Message
from pathlib import Path
from secrets import compare_digest

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPBasic
from lxml import etree as xml
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from runtime import app, engine, setting

SOAP = "http://www.w3.org/2003/05/soap-envelope"
REV = "urn:mahasetu:revenue:v1"
S, R = "{" + SOAP + "}", "{" + REV + "}"
CONTRACT = Path(__file__).parent / "contracts/v1"
SCHEMA = xml.XMLSchema(xml.parse(str(CONTRACT / "revenue.xsd")))
AUTH = HTTPBasic(auto_error=False)
USER = setting("REVENUE_USER").encode()
PASSWORD = setting("REVENUE_PASSWORD").encode()


def child(parent, tag, value=None):
    node = xml.SubElement(parent, tag)
    if value is not None:
        node.text = str(value)
    return node


def envelope():
    root = xml.Element(S + "Envelope", nsmap={"s": SOAP, "r": REV})
    return child(root, S + "Body")


def send(body, status=200, headers=None):
    return Response(xml.tostring(body.getroottree(), encoding="utf-8"), status,
                    media_type="application/soap+xml", headers=headers)


def fault(status, code, message, reference="unknown", soap_code=None):
    body = envelope()
    node = child(body, S + "Fault")
    child(child(node, S + "Code"), S + "Value", "s:" + (soap_code or ("Receiver" if status >= 500 else "Sender")))
    reason = child(child(node, S + "Reason"), S + "Text", message)
    reason.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
    detail = child(child(node, S + "Detail"), R + "ProviderFault")
    category = {401: "AUTHENTICATION", 404: "MISSING", 503: "PROVIDER", 500: "INTERNAL"}.get(status, "INPUT")
    for key, value in [("Code", code), ("Category", category), ("Message", message),
                       ("RequestReference", reference), ("Retryable", str(status == 503).lower()),
                       ("Timestamp", datetime.now(UTC).isoformat())]:
        child(detail, R + key, value)
    return send(body, status, {"WWW-Authenticate": "Basic"} if status == 401 else None)


@app.get("/soap/revenue.xsd")
def xsd():
    return FileResponse(CONTRACT / "revenue.xsd", media_type="application/xml")


@app.get("/soap/v1")
def wsdl(request: Request):
    if "wsdl" not in request.query_params:
        return fault(400, "WSDL_QUERY_REQUIRED", "Use ?wsdl to retrieve the contract")
    definition = xml.parse(str(CONTRACT / "revenue.wsdl"))
    address = definition.find(".//{http://schemas.xmlsoap.org/wsdl/soap12/}address")
    address.set("location", str(request.url.replace(query="")))
    return Response(xml.tostring(definition), media_type="application/xml")


def lookup(operation, reference):
    student = operation.findtext(R + "StudentID")
    requested = operation.findtext(R + "CertificateType")
    body = envelope()
    result = child(body, R + "GetStudentCertificatesResponse")
    child(result, R + "StudentID", student)
    child(result, R + "RequestReference", reference)
    found = False
    with engine.connect() as db:
        for kind, field, tag in [("Income", "annual_income", "AnnualIncomeINR"), ("Caste", "caste_category", "Category")]:
            if requested and requested != kind.upper():
                continue
            # Identifiers come exclusively from the two contract-defined certificate types.
            row = db.execute(text(f"""SELECT certificate_ref, status, issued_on, expires_on, {field}
                FROM revenue.{kind.lower()}_certificates WHERE student_id=:student
                ORDER BY issued_on DESC, certificate_ref DESC LIMIT 1"""), {"student": student}).mappings().first()
            if row:
                found = True
                status = row["status"]
                if status == "VALID" and row["expires_on"] < datetime.now(UTC).date():
                    status = "EXPIRED"
                cert = child(result, R + kind + "Certificate")
                for name, value in [("ProviderRecordReference", row["certificate_ref"]), ("CertificateStatus", status),
                                    ("IssueDate", row["issued_on"]), ("ExpiryDate", row["expires_on"]), (tag, row[field])]:
                    child(cert, R + name, value)
    if not found:
        return fault(404, "RECORD_MISSING", "Requested certificate unavailable", reference)
    SCHEMA.assertValid(result)
    return send(body)


@app.post("/soap/v1")
async def dispatch(request: Request):
    reference = "unknown"
    try:
        try:
            credentials = await AUTH(request)
        except HTTPException:
            credentials = None
        if not credentials or not (compare_digest(credentials.username.encode(), USER)
                                   & compare_digest(credentials.password.encode(), PASSWORD)):
            return fault(401, "INVALID_CREDENTIALS", "Service authentication required")
        media = Message()
        media["Content-Type"] = request.headers.get("content-type", "")
        if media.get_content_type() != "application/soap+xml":
            return fault(415, "UNSUPPORTED_MEDIA", "Expected SOAP 1.2 content type")
        payload = bytearray()
        async for chunk in request.stream():
            if len(payload) + len(chunk) > 65536:
                return fault(413, "REQUEST_TOO_LARGE", "SOAP message exceeds size limit")
            payload.extend(chunk)
        root = xml.fromstring(bytes(payload), xml.XMLParser(resolve_entities=False, load_dtd=False,
                                                            no_network=True, remove_comments=True, remove_pis=True))
        if root.getroottree().docinfo.doctype:
            return fault(400, "INVALID_XML", "Document type declarations are prohibited")
        if root.tag != S + "Envelope":
            return fault(400, "INVALID_ENVELOPE", "Expected SOAP 1.2 Envelope", soap_code="VersionMismatch")
        if [n.tag for n in root] not in ([S + "Body"], [S + "Header", S + "Body"]):
            return fault(400, "INVALID_ENVELOPE", "Expected one SOAP Body")
        header = root.find(S + "Header")
        if header is not None and any(h.get(S + "mustUnderstand") in ("1", "true") for h in header):
            return fault(400, "UNSUPPORTED_HEADER", "Mandatory header unsupported", soap_code="MustUnderstand")
        body = root.find(S + "Body")
        if len(body) != 1 or body[0].tag != R + "GetStudentCertificates":
            return fault(400, "UNSUPPORTED_OPERATION", "Unknown SOAP operation")
        if media.get_param("action") not in (None, REV + "/GetStudentCertificates"):
            return fault(400, "UNSUPPORTED_ACTION", "Unrecognized SOAP action")
        op = body[0]
        if not SCHEMA.validate(op):
            return fault(400, "INVALID_REQUEST", "Request does not match the Revenue schema")
        reference = op.findtext(R + "RequestReference")
        if not reference or len(reference) > 256:
            return fault(400, "INVALID_REFERENCE", "Invalid request reference")
        return await run_in_threadpool(lookup, op, reference)
    except xml.XMLSyntaxError:
        return fault(400, "INVALID_XML", "Malformed XML")
    except SQLAlchemyError:
        return fault(503, "DATABASE_UNAVAILABLE", "Department database unavailable", reference)
    except Exception:
        return fault(500, "INTERNAL_ERROR", "Unexpected provider error", reference)
