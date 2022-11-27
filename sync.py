from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

def init_scheduler():
    scheduler = AsyncIOScheduler()

    from service.scheduler.start_node import start_node
    from service.scheduler.check_sync import check_sync
    from service.scheduler.add_peers import add_peers

    scheduler.add_job(start_node, "interval", minutes=1)
    scheduler.add_job(check_sync, "interval", minutes=1)
    scheduler.add_job(add_peers, "interval", minutes=1)
    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    init_scheduler()
