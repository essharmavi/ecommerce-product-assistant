from .custom_logger import CustomLogger
GLOBAL_LOGGER = CustomLogger().get_logger("ecomm-prod-assistant")  # Single global logger instance