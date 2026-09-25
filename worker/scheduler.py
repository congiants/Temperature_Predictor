from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from aggregator import run_aggregation
from predictor import run_prediction


def daily_job():
    print(datetime.now(), "daily job starting")
    try:
        run_aggregation()
        run_prediction()
    except Exception as e:
        print(datetime.now(), "daily job FAILED:", e)


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Europe/Athens")
    #scheduler.add_job(daily_job, "interval", minutes=1)
    scheduler.add_job(daily_job, "cron", hour=0, minute=10)
    print("Scheduler started, next run 03:10")
    scheduler.start()