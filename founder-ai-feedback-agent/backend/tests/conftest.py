"""Pytest configuration and shared fixtures."""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.database import Base, get_db

TEST_DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/founder_ai_feedback_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_feedback_texts():
    return [
        "The app keeps crashing whenever I try to make a payment. This is unacceptable!",
        "I love the new dashboard design. It's so much easier to use now.",
        "Please add dark mode, it would make the app so much better to use at night.",
        "Customer support took 5 days to respond and still didn't solve my problem.",
        "The loading time is too slow. It takes forever to open the reports page.",
        "Would love to have a mobile app for iOS and Android.",
        "Login keeps failing with 2FA. I've been locked out for 3 days.",
        "Overall a great product, very happy with the features.",
        "Can you please add CSV export functionality? It's really needed.",
        "The billing page is confusing and I was charged twice this month.",
    ]
