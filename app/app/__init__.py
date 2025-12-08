from fastapi import FastAPI
from app import routes
from app.database import engine
from app.models import Base
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("App is starting...")

Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(routes.router)