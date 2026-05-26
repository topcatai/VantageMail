# -*- coding: utf-8 -*-
from services.providers.imap_provider import _has_attachments_from_structure

def test_has_attachments_from_structure_flat_no():
    struct = (b'TEXT', b'PLAIN', (b'CHARSET', b'US-ASCII'), None, None, b'7BIT', 100, 5)
    assert not _has_attachments_from_structure(struct)

def test_has_attachments_from_structure_flat_yes():
    struct = (b'APPLICATION', b'PDF', (b'NAME', b'test.pdf'), None, None, b'BASE64', 5000)
    assert _has_attachments_from_structure(struct)

def test_has_attachments_from_structure_multipart_mixed():
    struct = [
        (b'TEXT', b'HTML', (b'CHARSET', b'UTF-8'), None, None, b'8BIT', 1000, 20),
        (b'APPLICATION', b'OCTET-STREAM', (b'NAME', b'document.docx'), None, None, b'BASE64', 15000),
        b'MIXED'
    ]
    assert _has_attachments_from_structure(struct)

def test_has_attachments_from_structure_disposition():
    struct = (
        b'IMAGE', b'PNG', (b'NAME', b'img.png'), None, None, b'BASE64', 1000, None, 
        (b'ATTACHMENT', (b'FILENAME', b'img.png'))
    )
    assert _has_attachments_from_structure(struct)
