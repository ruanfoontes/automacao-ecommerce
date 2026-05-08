import requests
import os
import pandas as pd
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass # No Cloud funcionará via Secrets