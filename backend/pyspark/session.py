from pyspark.sql import SparkSession
import logging

logger = logging.getLogger(__name__)

_spark = None

def get_spark_session(app_name: str = "OptiGene") -> SparkSession:
    """
    Returns a singleton SparkSession configured for local execution.
    """
    global _spark
    if _spark is None:
        try:
            logger.info("Initializing SparkSession...")
            _spark = SparkSession.builder \
                .appName(app_name) \
                .master("local[*]") \
                .config("spark.driver.memory", "4g") \
                .config("spark.sql.shuffle.partitions", "4") \
                .config("spark.ui.showConsoleProgress", "false") \
                .getOrCreate()
            
            # Mute INFO log level from PySpark to clean console output
            _spark.sparkContext.setLogLevel("WARN")
            logger.info("SparkSession successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize SparkSession: {e}")
            raise e
    return _spark

def stop_spark_session():
    """
    Stops the active SparkSession.
    """
    global _spark
    if _spark is not None:
        try:
            logger.info("Stopping SparkSession...")
            _spark.stop()
            _spark = None
            logger.info("SparkSession stopped.")
        except Exception as e:
            logger.error(f"Failed to stop SparkSession: {e}")
