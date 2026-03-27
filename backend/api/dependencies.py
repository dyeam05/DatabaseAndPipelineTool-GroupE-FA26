from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def get_session_local(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_local


async def get_session(
    session_local: async_sessionmaker[AsyncSession] = Depends(get_session_local)
) -> AsyncGenerator[AsyncSession, None]:
    async with session_local() as session:
        yield session


async def get_transactional_session(
    session_local: async_sessionmaker[AsyncSession] = Depends(get_session_local)
) -> AsyncGenerator[AsyncSession, None]:
    async with session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
