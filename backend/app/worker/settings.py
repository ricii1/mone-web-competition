from arq.connections import RedisSettings

from app.core.config import settings
from app.worker.jobs.generate_content import generate_levels_and_questions
from app.worker.jobs.material import process_material


class WorkerSettings:
    functions = [process_material, generate_levels_and_questions]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = settings.worker_max_jobs
