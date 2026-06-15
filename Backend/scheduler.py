from apscheduler.schedulers.background import BackgroundScheduler
from ai_agent import run_hourly_agent

# Initialize the scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """
    Adds the AI agent job to the scheduler and starts it.
    We set it to run at the top of every hour (minute=0).
    For testing purposes, you can change 'hours=1' to 'minutes=1'.
    """
    # Runs exactly once an hour
    scheduler.add_job(run_hourly_agent, 'interval', hours=20, id='ai_hourly_agent', replace_existing=True)
    scheduler.start()
    print("APScheduler started: AI Agent will run every hour.")

def stop_scheduler():
    """Gracefully shuts down the scheduler."""
    scheduler.shutdown()
    print("APScheduler stopped.")
