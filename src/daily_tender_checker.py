#!/usr/bin/env python3
import subprocess
import datetime
import logging
import os
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent  # Adjust this if needed
sys.path.append(str(project_root))

# Set up logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"tender_check_{datetime.datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("daily_tender_checker")

def run_daily_check():
    """Run the tender download script for today's date across all regions."""
    try:
        # Get today's date
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Define regions - all Russian regions (1-99)
        # Using your structure for regions 1-9 with leading zeros
        regions = []
        for i in range(1, 100):
            if i < 10:
                regions.append(f'0{i}')
            else:
                regions.append(str(i))
                
        regions_str = ' '.join(regions)
        
        # Command to run the download_tenders.py script
        cmd = f"cd {project_root} && python ./src/download_tenders.py --regions {regions_str} --start-date {today} --end-date {today} --save_xml"
        
        logger.info(f"Starting tender check for date: {today}")
        logger.info(f"Running command: {cmd}")
        
        # Execute the command
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Tender check completed successfully")
            logger.debug(f"Output: {result.stdout}")
        else:
            logger.error(f"Tender check failed with return code: {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            
        # Optionally, run vectorization periodically (e.g., once a week)
        # Uncomment and modify as needed
        # if datetime.datetime.now().weekday() == 6:  # Sunday
        #     logger.info("Running weekly vectorization")
        #     vectorize_cmd = "python download_tenders.py --vectorize --model-type roberta"
        #     vectorize_result = subprocess.run(vectorize_cmd, shell=True, capture_output=True, text=True)
        #     if vectorize_result.returncode == 0:
        #         logger.info("Vectorization completed successfully")
        #     else:
        #         logger.error(f"Vectorization failed: {vectorize_result.stderr}")
            
    except Exception as e:
        logger.exception(f"An error occurred during daily tender check: {str(e)}")

if __name__ == "__main__":
    run_daily_check()