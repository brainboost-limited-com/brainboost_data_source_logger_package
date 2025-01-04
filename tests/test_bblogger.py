# tests/test_bblogger.py

import pytest
from unittest import mock
from unittest.mock import patch
import os
import csv
from brainboost_data_source_logger_package.BBLogger import BBLogger
from brainboost_data_source_logger_package.BBLogEntry import BBLogEntry

from datetime import datetime
from io import StringIO


def list_to_csv_string(lst, delimiter='|', quotechar='"'):
    output = StringIO()
    writer = csv.writer(
        output,
        delimiter=delimiter,
        quotechar=quotechar,
        quoting=csv.QUOTE_ALL,  # Changed to QUOTE_ALL for consistency
        lineterminator=''
    )
    writer.writerow(lst)
    return output.getvalue()


@pytest.fixture
def config_fixture(request):
    """
    Fixture to provide configuration for BBLogger.
    """
    # Determine the directory of the current test file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    # Define the log_path as 'tests/logs' within the project directory
    log_path = os.path.join(test_dir, 'logs')

    # Define the log file name based on the current date
    current_date = datetime.now().strftime('%Y_%m_%d')
    log_file_name = f"worktwins_log_{current_date}.log"
    log_file_path = os.path.join(log_path, log_file_name)

    config_dict = {
        'log_path': log_path,
        'log_path_ocr': 'com_worktwins_userdata/com_worktwins_ocr',
        'log_path_images': 'com_worktwins_userdata/com_worktwins_images',
        'log_base_url_1_5': 'http://100.96.1.34:8080/log',
        'log_debug_mode': True,
        'log_telegram_service_url': 'http://0.0.0.0:8080/send_telegram_notification',
        'log_enable_storage': True,
        'log_terminal_output': True,
        'log_delimiter': '|',
        'sqlite3_storage_enabled': False,
        'sqlite3_storage_path': 'com_worktwins_userdata/logs.db',
        'page_size': 100,
        'log_header': ['timestamp', 'type', 'process_name', 'source_code_line', 'message', 'exec_time'],
        'memsize_limit': 50 * 1024 * 1024
    }

    # Create the 'tests/logs' directory if it doesn't exist
    os.makedirs(config_dict['log_path'], exist_ok=True)

    return config_dict


@pytest.fixture(autouse=True)
def clean_log_directory(config_fixture):
    """
    Automatically clean the log directory before each test.
    """
    log_path = config_fixture.get('log_path')
    if log_path and os.path.exists(log_path):
        for root, dirs, files in os.walk(log_path, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except Exception as e:
                    print(f"Failed to remove file {name}: {e}")
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception as e:
                    print(f"Failed to remove directory {name}: {e}")


@patch('brainboost_data_source_logger_package.BBLogger.requests.get')
def test_BBLogger_log(mock_requests_get, config_fixture, capsys):
    """
    Test the BBLogger.log method.
    """

    # Prepare mock for external logging and Telegram notification
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    # Log a test message without outputting to console
    test_message = "This is a test log message."
    BBLogger.log(
        message=test_message,
        log_type='message',
        telegram=True,  # Set to True to trigger external logging
        public=False,
        trace=False,
        output_to_console=False  # Set to False; do not print to console
    )

    # Verify that external logging was called once
    mock_requests_get.assert_called_once()
    call_args, call_kwargs = mock_requests_get.call_args
    assert call_args[0] == config_fixture['log_telegram_service_url'], "Telegram service URL mismatch."
    assert call_kwargs['timeout'] == 5, "Timeout parameter mismatch."
    assert 'message' in call_kwargs['params'], "Message parameter missing."
    assert test_message in call_kwargs['params']['message'], "Log message not found in Telegram params."

    # Verify that the log file was created
    current_date = datetime.now().strftime('%Y_%m_%d')
    log_file_path = os.path.join(config_fixture['log_path'], f'worktwins_log_{current_date}.log')
    assert os.path.isfile(log_file_path), f"Log file was not created at path: {log_file_path}"

    # Verify the contents of the log file
    with open(log_file_path, 'r', encoding='utf-8', newline='') as log_file:
        reader = csv.reader(log_file, delimiter=config_fixture['log_delimiter'], quotechar='"')
        rows = list(reader)
        assert len(rows) == 2, "Log file should contain header and one log entry."
        header, log_entry = rows
        assert header == config_fixture['log_header'], "Header row does not match."
        assert len(log_entry) == 6, "Log entry should have 6 fields."
        timestamp_str, log_type, process_name, code_location, message, exec_time = log_entry
        assert log_type == 'message', "Log type should be 'message'."
        assert message == test_message, "Log message does not match."

    # Capture and verify terminal output
    captured = capsys.readouterr()
    assert test_message not in captured.out, "Terminal output should not contain the log message when output_to_console=False."


@patch('brainboost_data_source_logger_package.BBLogger.requests.get')
def test_BBLogger_log_error(mock_requests_get, config_fixture, capsys):
    """
    Test the BBLogger.log method with an error message.
    """
    # Configure BBLogger with the fixture
    BBLogger.configure(config_fixture)

    # Prepare mock for external logging and Telegram notification
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    # Log an error message without outputting to console
    test_error_message = "An error occurred during processing."
    BBLogger.log(
        message=test_error_message,
        log_type='message',  # Initially set as 'message'
        telegram=True,  # Set to True to trigger external logging
        public=True,
        trace=True,
        output_to_console=False,  # Do not print to console
        exc_info=(ValueError, ValueError("Test exception"), None)
    )

    # Verify that external logging was called once
    mock_requests_get.assert_called_once()
    call_args, call_kwargs = mock_requests_get.call_args
    assert call_args[0] == config_fixture['log_telegram_service_url'], "Telegram service URL mismatch."
    assert call_kwargs['timeout'] == 5, "Timeout parameter mismatch."
    assert 'message' in call_kwargs['params'], "Message parameter missing."
    assert test_error_message in call_kwargs['params']['message'], "Log message not found in Telegram params."

    # Verify that the log file was created
    current_date = datetime.now().strftime('%Y_%m_%d')
    log_file_path = os.path.join(config_fixture['log_path'], f'worktwins_log_{current_date}.log')
    assert os.path.isfile(log_file_path), f"Log file was not created at path: {log_file_path}"

    # Verify the contents of the log file
    with open(log_file_path, 'r', encoding='utf-8', newline='') as log_file:
        reader = csv.reader(log_file, delimiter=config_fixture['log_delimiter'], quotechar='"')
        rows = list(reader)
        assert len(rows) == 2, "Log file should contain header and one log entry."
        header, log_entry = rows
        assert header == config_fixture['log_header'], "Header row does not match."
        assert len(log_entry) == 6, "Log entry should have 6 fields."
        timestamp_str, log_type, process_name, code_location, message, exec_time = log_entry
        assert log_type == 'error', "Log type should be 'error'."
        assert test_error_message in message, "Log message does not contain the error message."
        assert 'Traceback' in message, "Traceback information was not appended to the message."

    # Capture and verify terminal output
    captured = capsys.readouterr()
    assert test_error_message not in captured.out, "Terminal output should not contain the error message when output_to_console=False."
    assert "Traceback" not in captured.out, "Terminal output should not contain traceback information when output_to_console=False."


@patch('brainboost_data_source_logger_package.BBLogger.requests.get')
def test_BBLogger_create_log_file_and_insert_entry(mock_requests_get, config_fixture, capsys):
    """
    Test that BBLogger creates a log file if it does not exist and inserts log entries correctly.
    """
    # Define the test message
    test_message = "Test log entry creation."

    # Ensure the log file does not exist before logging
    current_date = datetime.now().strftime('%Y_%m_%d')
    log_file_path = os.path.join(config_fixture['log_path'], f'worktwins_log_{current_date}.log')

    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    assert not os.path.isfile(log_file_path), f"Log file should not exist before logging at path: {log_file_path}"

    # Configure BBLogger with the fixture
    BBLogger.configure(config_fixture)

    # Prepare mock for external logging and Telegram notification
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    # Log the test message
    BBLogger.log(
        message=test_message,
        log_type='message',
        telegram=True,  # Set to True to trigger external logging
        public=False,
        trace=False,
        output_to_console=False  # Do not print to console
    )

    # Verify that external logging was called once
    mock_requests_get.assert_called_once()
    call_args, call_kwargs = mock_requests_get.call_args
    assert call_args[0] == config_fixture['log_telegram_service_url'], "Telegram service URL mismatch."
    assert call_kwargs['timeout'] == 5, "Timeout parameter mismatch."
    assert 'message' in call_kwargs['params'], "Message parameter missing."
    assert test_message in call_kwargs['params']['message'], "Log message not found in Telegram params."

    # Verify that the log file was created
    assert os.path.isfile(log_file_path), f"Log file was not created at path: {log_file_path}"

    # Verify the contents of the log file
    with open(log_file_path, 'r', encoding='utf-8', newline='') as log_file:
        reader = csv.reader(log_file, delimiter=config_fixture['log_delimiter'], quotechar='"')
        rows = list(reader)
        assert len(rows) == 2, "Log file should contain header and one log entry."
        header, log_entry = rows
        assert header == config_fixture['log_header'], "Header row does not match."
        assert len(log_entry) == 6, "Log entry should have 6 fields."
        timestamp_str, log_type, process_name, code_location, message, exec_time = log_entry
        assert log_type == 'message', "Log type should be 'message'."
        assert message == test_message, "Log message does not match."

    # Capture and verify terminal output
    captured = capsys.readouterr()
    assert test_message not in captured.out, "Terminal output should not contain the log message when output_to_console=False."
