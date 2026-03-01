"""
Fixtures de teste para NOVO CR.

Contém:
- DocumentFactory: Geração de documentos de teste
"""

from .document_factory import DocumentFactory, DocumentQuality, DocumentFormat, TestDocument

__all__ = ["DocumentFactory", "DocumentQuality", "DocumentFormat", "TestDocument"]
