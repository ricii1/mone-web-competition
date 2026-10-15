from arq.connections import RedisSettings

from app.core.config import settings
from app.worker.jobs.generate_content import generate_levels_and_questions
from app.worker.jobs.material import process_material
from app.worker.recovery import GENERATION_TIMEOUT_SECONDS, recover_stale_generations


class WorkerSettings:
    on_startup = recover_stale_generations
    functions = [process_material, generate_levels_and_questions]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = settings.worker_max_jobs
    # Long PDFs need 1-2 LLM calls per level; arq's default of 300s is too short.
    job_timeout = GENERATION_TIMEOUT_SECONDS
