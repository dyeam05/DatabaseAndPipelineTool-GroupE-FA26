from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.job_segment_run import JobSegmentRun

class JobSegmentRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        
    async def get_by_id(
        self, 
        job_run_num:int, 
        job_def_id:int, 
        route_id:str, 
        segment_id:int
    ) -> JobSegmentRun | None:
        return await self._session.get(JobSegmentRun, {
            "job_run_num":job_run_num, 
            "job_def_id": job_def_id, 
            "route_id": route_id,
            "segment_id": segment_id
        })
        
    
        