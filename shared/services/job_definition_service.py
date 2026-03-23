from db.models.job_definition import JobDefinition, JobType
from repositories.job_definition_repository import JobDefinitionRepository
from services.errors import JobDefinitionAlreadyExistsError, JobDefinitionNotFoundError

# This service is responsible for managing job definitions, which are templates for creating jobs.(maybe)
class JobDefinitionService:
    def __init__(self, job_definition_repository: JobDefinitionRepository) -> None:
        self._job_definition_repository = job_definition_repository

    async def list_job_definitions(self) -> list[JobDefinition]:
        return await self._job_definition_repository.list_all()

    async def get_job_definitions_by_type(self, type: JobType) -> list[JobDefinition]:
        return await self._job_definition_repository.get_by_type(type)

    async def get_job_definition(self, job_def_id: int) -> JobDefinition | None:
        return await self._job_definition_repository.get_by_id(job_def_id)

    async def create_job_definition(
        self,
        type: JobType, # go job detection as such
        name: str,
        config: dict,
        description: str | None = None,
    ) -> JobDefinition:
        return await self._job_definition_repository.create(
            type=type,
            name=name,
            config=config,
            description=description,
        )

    async def delete_job_definition(self, job_def_id: int) -> None:
        job_definition = await self._job_definition_repository.get_by_id(job_def_id)
        if job_definition is None:
            raise JobDefinitionNotFoundError(job_def_id)

        await self._job_definition_repository.delete(job_definition)