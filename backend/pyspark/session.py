from pyspark.sql import SparkSession
import logging

logger = logging.getLogger(__name__)

_spark = None

def get_spark_session(app_name: str = "OptiGene") -> SparkSession:
    """
    Mengembalikan SparkSession singleton yang dikonfigurasi untuk local execution.
    """
    global _spark
    if _spark is None:
        try:
            logger.info("Menginisialisasi SparkSession...")
            _spark = SparkSession.builder \
                .appName(app_name) \
                .master("local[*]") \
                .config("spark.driver.memory", "4g") \
                .config("spark.sql.shuffle.partitions", "4") \
                .config("spark.ui.showConsoleProgress", "false") \
                .getOrCreate()
            
            # Matikan log level INFO dari PySpark agar output konsol bersih
            _spark.sparkContext.setLogLevel("WARN")
            logger.info("SparkSession berhasil diinisialisasi.")
        except Exception as e:
            logger.error(f"Gagal menginisialisasi SparkSession: {e}")
            raise e
    return _spark

def stop_spark_session():
    """
    Menghentikan SparkSession aktif.
    """
    global _spark
    if _spark is not None:
        try:
            logger.info("Menghentikan SparkSession...")
            _spark.stop()
            _spark = None
            logger.info("SparkSession dihentikan.")
        except Exception as e:
            logger.error(f"Gagal menghentikan SparkSession: {e}")
