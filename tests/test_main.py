from unittest.mock import patch, MagicMock
from main import main

@patch('main.uvicorn.run')
@patch('main.process_scans')
@patch('main.load_detection_model')
def test_main_calls(mock_load, mock_process, mock_uvicorn_run):
    mock_model = MagicMock()
    mock_load.return_value = mock_model
    mock_process.return_value = ({}, {})
    main()
    mock_load.assert_called_once()
    mock_process.assert_called_once()
    mock_uvicorn_run.assert_called_once()