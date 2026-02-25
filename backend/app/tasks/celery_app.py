from celery import Celery
from celery.schedules import crontab
from ..settings import settings

celery = Celery("riskstack", broker=settings.redis_url, backend=settings.redis_url)

celery.conf.beat_schedule = {
    "refresh-sec-tickers-exchange": {
        "task": "app.tasks.jobs.refresh_sec_tickers_exchange",
        "schedule": crontab(hour=2, minute=10),
    },
}
