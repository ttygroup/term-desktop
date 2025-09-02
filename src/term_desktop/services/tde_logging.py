"tde_logging.py - Logging service."

from __future__ import annotations
from typing import TYPE_CHECKING, Any, TypedDict, NamedTuple
import logging
from pathlib import Path
import inspect
from collections import deque
# import platformdirs
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
from ezpubsub import Signal
from pythonjsonlogger.json import JsonFormatter

# Textual imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import AceOfBase #, ProcessContext, ProcessType

# Textual library imports
# None

# Local imports
# None



class LogPayload(TypedDict):
    """This is for the log signal. It can be subsribed to using
    the `subscribe_to_logs` method on the LoggingService.
    
    Required:
    - level: int
    - msg: str
    - exc_info: inspect.Traceback | None
    - session_id: int
    - group: str
    - path: str
    - line_number: int
    """
    
    level: int
    msg: str
    exc_info: inspect.Traceback | None
    session_id: int
    group: str
    path: str
    line_number: int
    
    
#? This class is copied from the textual devtools module.
# It's here so we can use it without needing the devtools package.
class DevtoolsLog(NamedTuple):
    objects_or_string: tuple[Any, ...] | str
    caller: inspect.Traceback
        

class HybridFIFOHandler(logging.FileHandler):
    def __init__(
        self,
        filename: Path,
        memory_buffer: deque[str],
        cleanup_interval: int = 100,
        **kwargs: Any,
    ):
        super().__init__(filename, mode="a", encoding="utf-8", **kwargs)
        self.filename = filename
        self.cleanup_interval = cleanup_interval
        self.message_count = 0
        self.memory_buffer = memory_buffer

        # Load existing logs into memory
        try:
            with open(self.filename, "r") as f:
                lines = f.readlines()
                for line in lines:
                    self.memory_buffer.append(line.strip())
        except FileNotFoundError:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)

        formatted = self.format(record)
        self.memory_buffer.append(formatted)
        self.message_count += 1

        # Periodic cleanup (expensive operation done rarely)
        if self.message_count % self.cleanup_interval == 0:
            try:
                # Use our memory buffer to rewrite file efficiently
                with open(self.filename, "w") as f:
                    for line in self.memory_buffer:
                        f.write(line + "\n")
            except (IOError, OSError):
                pass
                #! this should do something better.
    

class LoggerProcess(AceOfBase):
    
    def __init__(self, process_id: str, logs_dir: Path, max_lines:int = 1000) -> None:
        super().__init__()
        
        self.process_id = process_id
        self.memory_buffer: deque[str] = deque(maxlen=max_lines)
        
        self.tde_logger = logging.getLogger(process_id)
        self.tde_logger.setLevel(logging.DEBUG)

        # Every logging process will get its own log file.
        # There's only one default process at the moment, but I have
        # a feeling that this will be useful in the future.
        handler = HybridFIFOHandler(
            logs_dir / f"{self.process_id}.log",
            memory_buffer=self.memory_buffer,
            cleanup_interval=100,
        )
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        self.tde_logger.addHandler(handler)        

    def __call__(self, msg: str, level: int = logging.INFO, **kwargs: Any) -> LoggerProcess:
        """Log a message with the given level.

        Args:
            message (str): The message to log.
            level (int, optional): The logging level. Defaults to logging.INFO.
            **kwargs: Additional keyword arguments to pass to the logger.

        Returns:
            LoggerProcess: Returns self to allow for method chaining.
        """
            
        if 'exc_info' in kwargs:
            exc_info = kwargs.pop('exc_info')
        else:
            exc_info = None
            
        self.tde_logger.log(level, msg, exc_info=exc_info, **kwargs)
        
        return self

class LoggingService(TDEServiceBase[LoggerProcess]):

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "logging_service"
    logger_name = "tde_logger"

    def __init__(self, services_manager: ServicesManager) -> None:
        """
        Initialize the logging service
        """
        super().__init__(services_manager)
        
        self.logs_dir = self.services_manager.storage_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.max_lines = 1000  #* make this a config setting
        self.start_default_logger()
    
    def start_default_logger(self) -> None:
        
        # instance_num = self._get_available_instance_num(self.logger_name)
        # if instance_num == 1:
        #     process_id = self.logger_name
        # else:
        #     process_id = f"{self.logger_name}_{instance_num}"

        tde_logger_process = LoggerProcess(
            process_id=self.logger_name,
            logs_dir=self.logs_dir,
            max_lines=self.max_lines,
        )
        self._add_process_to_dict(tde_logger_process, self.logger_name)
        self.log_signal: Signal[LogPayload] = Signal("log_signal")
        
    ################
    # ~ Messages ~ #
    ################
    # None yet

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    @property
    def loggers(self) -> dict[str, LoggerProcess]:
        """Alias for self.processes on the Logging service"""
        return self.processes
    
    @property
    def logger(self) -> LoggerProcess:
        """Return the default logger process."""
        return self.processes[self.logger_name]
    
    @property
    def memory_buffer(self) -> deque[str]:
        """Get a copy of the default logger process memory buffer."""
        return self.processes[self.logger_name].memory_buffer.copy()
    
    @property
    def recent_logs(self) -> deque[str]:
        "Alias for self.memory_buffer"
        return self.memory_buffer
    
    def __call__(self, msg: str, *args: Any, **kwargs: Any) -> LoggerProcess:
        """Call the default logger process."""
        return self.processes[self.logger_name](msg, *args, **kwargs)

    async def start(self) -> bool:
        """Start the Logging service."""

        if len(self.processes) == 0:
            self.start_default_logger()
            return True
        else:
            if isinstance(self.processes.get(self.logger_name), LoggerProcess):
                return True
            else:
                return False

    async def stop(self) -> bool:
        self.log("Stopping Logging service")
        try:
            self.processes.clear()
            self.log_signal.clear()
        except Exception as e:
            raise e
        else:
            return True
        
    def subscribe_to_signal(self, callback: Any) -> None:
        """Subscribe to log messages."""
        self.log_signal.subscribe(callback)
        
    def publish_to_signal(self, log_payload: LogPayload) -> None:
        """Publish a log message to the signal."""
        self.log_signal.publish(log_payload)

    ################
    # ~ Internal ~ #
    ################
    # Methods that are only used inside this service.
    # These should be marked with a leading underscore.