from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()

db_password = os.getenv('db_password')
db_port = os.getenv('db_port')
db_name = os.getenv('db_name')
db_user = os.getenv('db_user')

# Database config
db_url = f"postgresql://{db_user}:{db_password}@Localhost:{db_port}/{db_name}"

# aws config
queue_url = "https://sqs.us-east-1.amazonaws.com/920441303945/data-engineering-case-analytics-queue"
queue_url = queue_url.strip().encode("ascii", "ignore").decode()
