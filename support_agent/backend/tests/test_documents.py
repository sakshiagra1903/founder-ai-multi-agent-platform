import pytest
from unittest.mock import patch

@pytest.fixture
def auth_headers(client):
    """Signs up a test user, logs them in, and returns headers with JWT token."""
    client.post(
        "/api/auth/signup",
        json={
            "name": "Doc User",
            "email": "doc@example.com",
            "password": "password123"
        }
    )
    response = client.post(
        "/api/auth/login",
        json={
            "email": "doc@example.com",
            "password": "password123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_documents_unauthorized(client):
    response = client.get("/api/documents")
    assert response.status_code == 401

def test_list_documents_authorized_empty(client, auth_headers):
    response = client.get("/api/documents", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_upload_invalid_file_type(client, auth_headers):
    # Try uploading a text file
    files = {"file": ("test.txt", b"dummy file content", "text/plain")}
    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "only PDF documents are supported" in response.json()["detail"].lower()

@patch("app.api.routes.documents.pdf_service.extract_text")
@patch("app.api.routes.documents.chunking_service.create_chunks")
@patch("app.api.routes.documents.vector_store_service.add_documents")
def test_upload_valid_pdf(mock_add_docs, mock_create_chunks, mock_extract_text, client, auth_headers):
    # Setup mocks
    mock_extract_text.return_value = [{"page_number": 1, "content": "Sample PDF content"}]
    mock_create_chunks.return_value = [{
        "chunk_id": "test_doc_p1_c0",
        "document_id": "test_doc",
        "page_number": 1,
        "content": "Sample PDF content"
    }]
    mock_add_docs.return_value = None

    # Perform upload
    files = {"file": ("test.pdf", b"%PDF-1.4 dummy contents", "application/pdf")}
    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "processed"
    assert "document_id" in data
