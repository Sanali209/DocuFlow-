from unittest.mock import patch


def test_gnc_parser_logs_on_unreadable_file(tmp_path):
    """GncParser.parse must log an error when the file cannot be read."""
    from docuflow.features.folder_scanner.parsers.gnc import GncParser

    parser = GncParser()
    nonexistent = tmp_path / "missing.GNC"

    with patch("docuflow.features.folder_scanner.parsers.gnc.logger") as mock_logger:
        result = parser.parse(nonexistent)

    # Must return empty GncSheet (graceful fallback preserved)
    assert result is not None

    # Must have logged the error
    assert mock_logger.error.called or mock_logger.warning.called, (
        "GncParser.parse must log when file cannot be read"
    )
