"""Tests for openvscode-server version resolution."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from portable_ovscode.cli import (
    FALLBACK_SERVER_VERSION,
    fetch_latest_server_version,
    resolve_server_version,
)


class _MockResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class TestVersionResolution(unittest.TestCase):
    def test_uses_explicit_server_version_without_lookup(self):
        with patch("portable_ovscode.cli.fetch_latest_server_version") as mock_fetch:
            version = resolve_server_version("1.95.3")
        self.assertEqual(version, "1.95.3")
        mock_fetch.assert_not_called()

    def test_fetch_latest_server_version_success(self):
        body = b'{"tag_name": "openvscode-server-v1.109.5"}'
        with patch(
            "portable_ovscode.cli.urllib.request.urlopen",
            return_value=_MockResponse(body),
        ):
            version = fetch_latest_server_version()
        self.assertEqual(version, "1.109.5")

    def test_fetch_latest_server_version_invalid_tag(self):
        body = b'{"tag_name": "v1.109.5"}'
        with patch(
            "portable_ovscode.cli.urllib.request.urlopen",
            return_value=_MockResponse(body),
        ):
            with self.assertRaises(RuntimeError):
                fetch_latest_server_version()

    def test_resolve_fallback_on_lookup_error(self):
        with (
            patch(
                "portable_ovscode.cli.fetch_latest_server_version",
                side_effect=RuntimeError("boom"),
            ),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
        ):
            version = resolve_server_version(None)
        self.assertEqual(version, FALLBACK_SERVER_VERSION)
        self.assertIn("WARNING: latest version lookup failed", stderr.getvalue())

    def test_resolve_no_warning_on_successful_lookup(self):
        with (
            patch(
                "portable_ovscode.cli.fetch_latest_server_version",
                return_value="1.109.5",
            ),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
        ):
            version = resolve_server_version(None)
        self.assertEqual(version, "1.109.5")
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
