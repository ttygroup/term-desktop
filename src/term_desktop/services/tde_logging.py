"tde_logging.py - Logging service."

from __future__ import annotations
from typing import TYPE_CHECKING, Any, NamedTuple, TypedDict, Mapping
import logging
from pathlib import Path
import inspect
import json
from collections import deque
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from logging import _ExcInfoType, _SysExcInfoType #type: ignore
    
from ezpubsub import Signal
from pythonjsonlogger.json import JsonFormatter

# Textual imports
# import rich.repr
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import AceOfBase  # , ProcessContext, ProcessType

# Textual library imports
# None

# Local imports
# None


class LogPayload(TypedDict):
    """This is for the log signal. It can be subsribed to using
    the `subscribe_to_logs` method on the LoggingService.

    Required:
    - level: int
    - message: str
    - session_id: int
    - group: str
    - path: str
    - line_number: int
    - exc_info: inspect.Traceback | None
    """

    level: int
    message: str
    session_id: int
    group: str
    path: str
    line_number: int
    exc_info: inspect.Traceback | None


# ? This class is copied from the textual devtools module.
# It's here so we can use it without needing the devtools package.
class DevtoolsLog(NamedTuple):
    objects_or_string: tuple[Any, ...] | str
    caller: inspect.Traceback


class HybridFIFOHandler(logging.FileHandler):
    def __init__(
        self,
        filename: Path,
        logger_process: LoggerProcess,
        **kwargs: Any,
    ):
        super().__init__(filename, mode="a", encoding="utf-8", **kwargs)
        self.filename = filename
        self.logger_process = logger_process
        self.cleanup_interval = 100
        self.message_count = 0
        self.max_lines = logger_process.max_lines

        # Load existing logs into memory
        try:
            with open(self.filename, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            # If the file doesn't already exist, it's because
            # the logger is new. No problem.
            pass
        else:
            for line in lines[-self.max_lines:]:
                # convert line into logging.LogRecord object using json:
                json_line: dict[str, Any] = json.loads(line)
                log_record = self.logger_process.make_log_record(
                    name=json_line.get("name", ""),
                    level=json_line.get("level", logging.INFO),
                    pathname=json_line.get("path", ""),
                    lineno=json_line.get("line_number", 0),
                    msg=json_line.get("message", ""),
                    group=json_line.get("group", ""),
                )
                self.logger_process.memory_buffer.append(log_record)
                
            # Cleanup log file right away if its over limit
            existing_lines = len(lines)
            if existing_lines > self.max_lines:
                self.cleanup()


    def emit(self, record: logging.LogRecord) -> None:

        super().emit(record)
        self.logger_process.log_signal.publish(record)
        self.logger_process.memory_buffer.append(record)
        self.message_count += 1
        if self.message_count % self.cleanup_interval == 0:
            self.cleanup()
        
    def cleanup(self):
        """Periodic cleanup (expensive operation done rarely)"""
        
        try:
            # Use the memory buffer to rewrite file efficiently
            with open(self.filename, "w") as f:
                for log_record in self.logger_process.memory_buffer:
                    f.write(self.format(log_record) + "\n")
        except (IOError, OSError):
            pass
            #! this should probably do something better.


class LoggerProcess(AceOfBase):

    def __init__(self, process_id: str, logs_dir: Path, max_lines: int = 1000) -> None:
        super().__init__()

        self.process_id = process_id
        self.max_lines = max_lines
        self.memory_buffer: deque[logging.LogRecord] = deque(maxlen=max_lines)
        self.log_signal: Signal[logging.LogRecord] = Signal(f"{process_id}_signal")

        self.tde_logger = logging.getLogger(process_id)
        self.tde_logger.setLevel(logging.DEBUG)

        # Every logging process will get its own log file.
        # There's only one default process at the moment, but I have
        # a feeling that this will be useful in the future.
        handler = HybridFIFOHandler(
            logs_dir / f"{self.process_id}.log",
            logger_process=self,
        )
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        self.tde_logger.addHandler(handler)

    def log(  #  type: ignore
        self,
        msg: object,
        level: int = logging.INFO,
        *args: object,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None ,       
        **kwargs: Any,
    ) -> None: 
        """
        Log a message using this Logger Process.

        NOTE this is not the same as the log method everywhere else
        in TDE. This one ONLY uses this TDE Logger process, which bypasses
        the Textual devtools logging.
        """
        self.tde_logger.log(
            level,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )
        
    # def __call__(self) -> logging.Logger:
    #     return self.tde_logger
        
    def make_log_record(
        self,
        name: str,
        level: int,
        pathname: str,
        lineno: int,
        msg: str,
        group: str,
        exc_info: _SysExcInfoType | None = None,
    ) -> logging.LogRecord:

        return logging.LogRecord(
            name=name,
            level=level,
            pathname=pathname,
            lineno=lineno,
            msg=msg,
            args=(group,),
            exc_info=exc_info,
        )

    def subscribe_to_signal(self, callback: Any) -> None:
        """Subscribe to log messages."""
        self.log_signal.subscribe(callback)

    def publish_to_signal(self, log_record: logging.LogRecord) -> None:
        """Publish a log message to the signal."""
        self.log_signal.publish(log_record)


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
        self.max_lines = 1000  # * make this a config setting
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
        # self.log_signal: Signal[logging.LogRecord] = Signal("log_signal")

    ################
    # ~ Messages ~ #
    ################
    # None yet

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    def log(  #  type: ignore
        self,
        msg: object,
        level: int = logging.INFO,
        *args: object,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None ,       
        **kwargs: Any,
    ) -> None: 
        """
        Log a message using the Logger Service.

        NOTE this is not the same as the log method everywhere else
        in TDE. This one ONLY uses the logger service, which bypasses
        the Textual devtools logging.
        """
        self.logger.log(
            msg=msg,
            level=level,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    @property
    def loggers(self) -> dict[str, LoggerProcess]:
        """Alias for self.processes on the Logging service"""
        return self.processes

    @property
    def logger(self) -> LoggerProcess:
        """Return the default logger process."""
        return self.processes[self.logger_name]

    @property
    def memory_buffer(self) -> deque[logging.LogRecord]:
        """Get a copy of the default logger process memory buffer."""
        return self.processes[self.logger_name].memory_buffer.copy()

    @property
    def recent_logs(self) -> deque[logging.LogRecord]:
        "Alias for self.memory_buffer"
        return self.memory_buffer

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
            for process in self.processes.values():
                process.tde_logger.handlers.clear()
                process.log_signal.clear()
            self.processes.clear()
        except Exception as e:
            raise e
        else:
            return True

    def subscribe_to_signal(self, callback: Any, logger: str = "tde_logger") -> None:
        """Subscribe to log messages."""
        log_process = self.processes.get(logger)
        if log_process is not None:
            log_process.log_signal.subscribe(callback)
        else:
            raise ValueError(f"Logger '{logger}' not found.")

    def publish_to_signal(self, log_record: logging.LogRecord, logger: str = "tde_logger") -> None:
        """Publish a log message to the signal."""
        log_process = self.processes.get(logger)
        if log_process is not None:
            log_process.log_signal.publish(log_record)
        else:
            raise ValueError(f"Logger '{logger}' not found.")
        
    def unsubscribe_from_signal(self, callback: Any, logger: str = "tde_logger") -> None:
        """Unsubscribe from log messages."""
        log_process = self.processes.get(logger)
        if log_process is not None:
            log_process.log_signal.unsubscribe(callback)
        else:
            raise ValueError(f"Logger '{logger}' not found.")

    ################
    # ~ Internal ~ #
    ################
    # Methods that are only used inside this service.
    # These should be marked with a leading underscore.
