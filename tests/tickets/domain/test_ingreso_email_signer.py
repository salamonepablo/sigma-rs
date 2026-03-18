"""Pruebas del firmador de payloads de ingreso."""

from apps.tickets.domain.services.ingreso_email_signer import IngresoEmailSigner


def test_signer_verifies_valid_payload():
    payload = {
        "dispatch_id": "123",
        "entry_id": "456",
        "to_recipients": ["to@example.com"],
        "cc_recipients": [],
        "subject": "Ingreso 123",
        "body": "Body",
        "body_html": None,
        "pdf_url": "http://localhost/pdf?dispatch_id=123",
    }
    secret = "secret"

    signature = IngresoEmailSigner.sign(payload, secret)

    assert IngresoEmailSigner.verify(payload, signature, secret)


def test_signer_rejects_tampered_payload():
    payload = {
        "dispatch_id": "123",
        "entry_id": "456",
        "to_recipients": ["to@example.com"],
        "cc_recipients": [],
        "subject": "Ingreso 123",
        "body": "Body",
        "body_html": None,
        "pdf_url": "http://localhost/pdf?dispatch_id=123",
    }
    secret = "secret"
    signature = IngresoEmailSigner.sign(payload, secret)

    payload["subject"] = "Ingreso 999"

    assert not IngresoEmailSigner.verify(payload, signature, secret)
