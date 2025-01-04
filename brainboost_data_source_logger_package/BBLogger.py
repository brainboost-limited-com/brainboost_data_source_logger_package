# BBLogger.py

import traceback
from datetime import datetime
import requests
import os
import sys
from typing import Optional
import csv

from brainboost_data_source_logger_package.BBLogEntry import BBLogEntry  # Replace with actual import path
from brainboost_configuration_package.BBConfig import BBConfig

class BBLogger:
    _process_name: Optional[str] = None
    _last_time: Optional[datetime] = None
    _delta: Optional[datetime] = None


    @classmethod
    def _get_process_name(cls) -> str:
        if not cls._process_name: 
            cls._process_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        return cls._process_name



    @classmethod
    def log(cls, message,
            telegram: bool = False,
            slack: bool = False,
            url_notification: bool = False):

        def is_error_message(message):
            possible_error_words_in_message = ['error', 'exception', 'failed', 'missing']
            # Convert the message to lowercase for case-insensitive comparison
            lower_message = message.lower()
            # Check if any of the possible error words are in the message
            return any(word in lower_message for word in possible_error_words_in_message)
        
        def is_warning_message(message):
            possible_warning_words_in_message = ['warning']
            # Convert the message to lowercase for case-insensitive comparison
            lower_message = message.lower()
            # Check if any of the possible error words are in the message
            return any(word in lower_message for word in possible_warning_words_in_message)


        if is_error_message(message):
            log_type = 'error'
        else:
            if is_warning_message(message):
                log_type = 'warning'
            else:
                log_type = 'message


        if BBConfig.get('log_debug_mode'):

            # Time tracking
            cls._delta = datetime.now() - cls._last_time if cls._last_time else None
            cls._last_time = datetime.now()
            current_date = cls._last_time.strftime('%Y_%m_%d')

            # Extract caller information (file name and line number)
            stack = traceback.extract_stack()
            # The caller is two steps back in the stack
            if len(stack) >= 2:
                caller = stack[-2]
                file_name = os.path.basename(caller.filename)
                line_number = caller.lineno
                code_location = f"{file_name}:{line_number}"
            else:
                code_location = 'Unknown'

            # Process exc_info if provided
            if exc_info:
                if isinstance(exc_info, tuple) and len(exc_info) == 3:
                    traceback_info = ''.join(traceback.format_exception(*exc_info))
                else:
                    print("Invalid exc_info provided. It should be a tuple of (exc_type, exc_value, exc_traceback).")
                    traceback_info = None
            elif trace:
                # If trace flag is True but exc_info is not provided
                traceback_info = ''.join(traceback.format_stack())
            else:
                traceback_info = None

            # Create a BBLogEntry instance without 'description'
            log_entry = BBLogEntry(
                process=cls.get_process_name(),
                timestamp=cls._last_time.strftime('%Y%m%d%H%M%S'),
                log_type=log_type,
                message=message,
                processing_time=str(cls._delta.total_seconds()) if cls._delta else '0',
                code_location=code_location
            )
            # Include traceback information if available
            if traceback_info:
                log_entry.message += f'\nTraceback:\n{traceback_info}'

            # Determine current_date based on log_entry.timestamp
            try:
                log_timestamp = datetime.strptime(log_entry.timestamp, '%Y%m%d%H%M%S')
                current_date = log_timestamp.strftime('%Y_%m_%d')
            except ValueError:
                cls.log('Invalid timestamp format: ' + log_entry.timestamp, log_type='error')
                current_date = cls._last_time.strftime('%Y_%m_%d')  # Fallback to current date

            # Local logging to file
            if cls.log_enable_storage():
                cls._write_to_log_file(log_entry, current_date)

            # Telegram notification
            if cls._should_notify_telegram(telegram, public):
                cls._send_telegram_notification(str(log_entry), public)

            # Optional terminal output
            if cls.log_terminal_output_enabled():
                print(str(log_entry))



    @classmethod
    def _write_to_log_file(cls, log_entry: BBLogEntry, current_date: str):
        """
        Writes the log entry to a CSV-formatted log file.
        Inserts header row if the file is being created for the first time.
        """
        log_file_path = os.path.join(BBConfig.get('log_path'), BBConfig.get('log_prefix')+f'_log_{current_date}.log')
        file_exists = os.path.isfile(log_file_path)

        try:
            with open(log_file_path, 'a+', encoding='utf-8', newline='') as log_file:
                writer = csv.writer(
                    log_file,
                    delimiter=BBConfig.get('log_delimiter'),  # Use delimiter from config
                    quotechar="'",
                    quoting=csv.QUOTE_MINIMAL
                )
                if not file_exists:
                    # Write header row from config['log_header']
                    if hasattr(cls._config, 'log_header') and isinstance(BBConfig.get('log_header'), (list, tuple)):
                        writer.writerow(BBConfig.get('log_header'))
                    else:
                        print("Config does not have a valid 'log_header'. Skipping header row.")
                # Write the log entry row
                writer.writerow([
                    log_entry.timestamp,
                    log_entry.log_type,
                    log_entry.process,
                    log_entry.code_location,
                    log_entry.message,
                    log_entry.processing_time
                ])
        except IOError as e:
            print(f'Failed to write to log file: {e}')


