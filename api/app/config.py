import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "clef-flash")
CLOUD_MODEL = os.environ.get("CLOUD_MODEL", "glm-5.3-flash:cloud")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "llama3.2:3b")

JUDGE_URL = os.environ.get("JUDGE_URL", OLLAMA_URL)

PHI_THRESHOLD = float(os.environ.get("PHI_THRESHOLD", "0.20"))
URGENT_THRESHOLD = float(os.environ.get("URGENT_THRESHOLD", "0.50"))

PRESIDIO_ANALYZER_URL = os.environ.get("PRESIDIO_ANALYZER_URL", "http://localhost:5002")
PRESIDIO_ANONYMIZER_URL = os.environ.get("PRESIDIO_ANONYMIZER_URL", "http://localhost:5001")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://gate:gate_dev_password@localhost:5434/gate")