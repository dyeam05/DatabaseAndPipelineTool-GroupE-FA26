from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.job_definition import JobDefinition, JobType
# repo for managing JobDefinition entities in the database

class JobDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_def_id: int) -> JobDefinition | None:
        return await self._session.get(JobDefinition, job_def_id)

    async def list_all(self) -> list[JobDefinition]:
        stmt = select(JobDefinition).order_by(JobDefinition.created_at.desc()) # order by created_at in descending order to get the most recent job definitions first
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_type(self, type: JobType) -> list[JobDefinition]:
        stmt = (
            select(JobDefinition)
            .where(JobDefinition.type == type)
            .order_by(JobDefinition.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        type: JobType,
        implementation_key: str,
        name: str,
        config: dict,
        description: str | None = None,
    ) -> JobDefinition:
        job_definition = JobDefinition(
            type=type,
            implementation_key=implementation_key,
            name=name,
            description=description,
            config=config,
        )
        self._session.add(job_definition)
        await self._session.flush()
        return job_definition

    async def save(self, job_definition: JobDefinition) -> JobDefinition:
        self._session.add(job_definition)
        await self._session.flush()
        return job_definition

    async def delete(self, job_definition: JobDefinition) -> None:
        await self._session.delete(job_definition)
        await self._session.flush()
