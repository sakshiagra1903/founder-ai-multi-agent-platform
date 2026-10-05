import logging
from typing import List, Dict, Any, Optional, Set, Tuple

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.vector_store_service import vector_store_service
from app.repositories.ticket_repo import ticket_repo

logger = logging.getLogger(__name__)


class AgentToolContext:
    """
    Per-request mutable context shared by all tools invoked during a single
    agent run. Tools can't return structured data directly to the caller
    (their output must be text for the LLM), so we collect citations / side
    effects here and read them back after the graph finishes.
    """

    def __init__(self, user_id: str, question: str, db: Session):
        self.user_id = user_id
        self.question = question
        self.db = db
        self.sources: List[Dict[str, Any]] = []
        self._seen_citations: Set[Tuple[str, Any]] = set()
        self.ticket_created: Optional[Dict[str, Any]] = None

    def add_document_citation(self, filename: str, page: int) -> None:
        key = ("document", filename, page)
        if key not in self._seen_citations:
            self._seen_citations.add(key)
            self.sources.append({"document": filename, "page": page, "type": "document"})

    def add_web_citation(self, title: str, url: str) -> None:
        key = ("web", url)
        if key not in self._seen_citations:
            self._seen_citations.add(key)
            self.sources.append({"document": title or url, "page": 0, "type": "web", "url": url})


def build_tools(ctx: AgentToolContext) -> List[Any]:
    """Builds a fresh set of LangChain tool objects bound to this request's context."""

    @tool("search_knowledge_base")
    def search_knowledge_base(query: str) -> str:
        """Search the user's uploaded documents (internal knowledge base) for information
        relevant to the query. ALWAYS call this tool FIRST for any factual question before
        trying anything else, since answers grounded in the user's own documents are most
        trustworthy."""
        try:
            results = vector_store_service.search(query, top_k=settings.AGENT_KB_TOP_K)
        except Exception as e:
            logger.error(f"search_knowledge_base tool failed: {str(e)}")
            return "The knowledge base search failed due to an internal error."

        chunks = []
        for doc, score in results:
            if doc.metadata.get("document_id") == "system":
                continue
            filename = doc.metadata.get("filename", "Unknown Document")
            page = doc.metadata.get("page_number", 1)
            ctx.add_document_citation(filename, page)
            chunks.append(f"[Source: {filename}, page {page}]\n{doc.page_content}")

        if not chunks:
            return "No relevant information was found in the uploaded knowledge base for this query."
        return "\n\n---\n\n".join(chunks)

    @tool("web_search")
    def web_search(query: str) -> str:
        """Search the public web for current, general, or factual information that is NOT
        found in the internal knowledge base. Only use this after search_knowledge_base has
        been tried and did not return a sufficient answer."""
        if not settings.AGENT_WEB_SEARCH_ENABLED:
            return "Web search is disabled by the administrator."
        try:
            from langchain_community.tools import DuckDuckGoSearchResults

            search = DuckDuckGoSearchResults(output_format="list", num_results=4)
            raw_results = search.invoke(query)
        except Exception as e:
            logger.error(f"web_search tool failed: {str(e)}")
            return f"Web search failed: {str(e)}"

        if not raw_results:
            return "No web results were found for this query."

        formatted = []
        for r in raw_results:
            title = r.get("title", "Untitled result")
            link = r.get("link", "")
            snippet = r.get("snippet", "")
            ctx.add_web_citation(title, link)
            formatted.append(f"[{title}]({link})\n{snippet}")

        return "\n\n---\n\n".join(formatted)

    @tool("create_support_ticket")
    def create_support_ticket(subject: str, description: str) -> str:
        """Create a human support-escalation ticket. Use this ONLY as a last resort: when
        neither the knowledge base nor the web search could answer the question, OR when the
        user explicitly asks to talk to a human / file a complaint / escalate an issue.
        `subject` should be a short title, `description` should summarize the user's issue
        and what has already been tried."""
        if not settings.AGENT_TICKET_TOOL_ENABLED:
            return "Ticket escalation is disabled by the administrator."
        try:
            ticket = ticket_repo.create(
                ctx.db,
                user_id=ctx.user_id,
                subject=subject,
                description=description,
                source_question=ctx.question,
            )
        except Exception as e:
            logger.error(f"create_support_ticket tool failed: {str(e)}")
            return f"Failed to create a support ticket: {str(e)}"

        ctx.ticket_created = {"id": ticket.id, "subject": ticket.subject, "status": ticket.status}
        return (
            f"Support ticket #{ticket.id[:8]} created successfully "
            f"(subject: '{subject}'). Our support team will follow up soon."
        )

    tools = [search_knowledge_base]
    if settings.AGENT_WEB_SEARCH_ENABLED:
        tools.append(web_search)
    if settings.AGENT_TICKET_TOOL_ENABLED:
        tools.append(create_support_ticket)
    return tools
