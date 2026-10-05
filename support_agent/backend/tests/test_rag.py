import pytest
from unittest.mock import patch, MagicMock
from app.services.chunking_service import chunking_service

def test_chunking_service_splits_text():
    pages_data = [
        {"page_number": 1, "content": "This is page one text. " * 50},  # ~1100 chars
        {"page_number": 2, "content": "Short text."}
    ]
    
    chunks = chunking_service.create_chunks(pages_data, document_id="test-doc-id")
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["document_id"] == "test-doc-id"
        assert "chunk_id" in chunk
        assert "content" in chunk
        assert chunk["page_number"] in [1, 2]

@patch("app.api.routes.chat.agent_service.answer_question")
def test_chat_endpoint(mock_answer_question, client):
    # Setup mock agentic RAG response
    mock_answer_question.return_value = {
        "answer": "The capital of France is Paris.",
        "sources": [{"document": "france.pdf", "page": 2, "type": "document"}],
        "ticket": None,
    }

    # Setup user
    client.post(
        "/api/auth/signup",
        json={
            "name": "Chat User",
            "email": "chat@example.com",
            "password": "password123"
        }
    )
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "chat@example.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ask question
    response = client.post(
        "/api/chat",
        json={"question": "What is the capital of France?"},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The capital of France is Paris."
    assert data["sources"] == [{"document": "france.pdf", "page": 2, "type": "document", "url": None}]
