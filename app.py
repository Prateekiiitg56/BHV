"""Vercel entrypoint — exports `app` for serverless deployment."""
import os
from dotenv import load_dotenv

load_dotenv()

from bhv.full_app import create_app

app = create_app()
