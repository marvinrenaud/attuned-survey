
import sys
import os
import logging
from pathlib import Path

# Add project root to path
# Assuming script is run from project root or backend folder
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.src.main import create_app
from backend.src.services.cleanup import CleanupService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Entry point for cleanup job."""
    app = create_app()
    
    with app.app_context():
        try:
            CleanupService.run_all()
        except Exception as e:
            logger.error(f"Cleanup job failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
