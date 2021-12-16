"""Unit tests for prometheus-libvirt-exporter reactive script."""
import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock

layer_mock = mock.Mock()
sys.modules["charms.layer"] = layer_mock

prometheus_libvirt_exporter = importlib.import_module(
    "reactive.prometheus-libvirt-exporter"
)

local_profile_no_change = """# Rule is already present
deny ptrace (read) peer=snap.prometheus-libvirt-exporter.daemon,
"""

local_profile_change = """# Rule is not present
"""


class TestLibvirtdApparmorLocalProfile(unittest.TestCase):
    """Test libvirtd apparmor local profile updates."""

    def setUp(self):  # noqa: D102
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.libvirtd_apparmor_local_profile = temp_file.name

    def tearDown(self):  # noqa: D102
        os.remove(self.libvirtd_apparmor_local_profile)

    @mock.patch("reactive.prometheus-libvirt-exporter.subprocess.check_call")
    def test_no_change(self, check_call):  # noqa: D102
        open(self.libvirtd_apparmor_local_profile, "w").write(local_profile_no_change)
        prometheus_libvirt_exporter.configure_libvirtd_apparmor_local_profile(
            self.libvirtd_apparmor_local_profile
        )

        actual_lines = list(
            map(str.strip, open(self.libvirtd_apparmor_local_profile, "r").readlines())
        )
        expected_lines = [
            "# Rule is already present",
            "deny ptrace (read) peer=snap.prometheus-libvirt-exporter.daemon,",
        ]

        self.assertEqual(actual_lines, expected_lines)
        check_call.assert_not_called()

    @mock.patch("reactive.prometheus-libvirt-exporter.subprocess.check_call")
    def test_change(self, check_call):  # noqa: D102
        open(self.libvirtd_apparmor_local_profile, "w").write(local_profile_change)
        prometheus_libvirt_exporter.configure_libvirtd_apparmor_local_profile(
            self.libvirtd_apparmor_local_profile
        )

        actual_lines = list(
            map(str.strip, open(self.libvirtd_apparmor_local_profile, "r").readlines())
        )
        expected_lines = [
            "# Rule is not present",
            "deny ptrace (read) peer=snap.prometheus-libvirt-exporter.daemon,",
        ]

        self.assertEqual(actual_lines, expected_lines)
        check_call.assert_called_with(
            ["/sbin/apparmor_parser", "-r", "/etc/apparmor.d/usr.sbin.libvirtd"]
        )
