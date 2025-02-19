"""Encapsulate prometheus-libvirt-exporter testing."""

import logging
import os
import re
import subprocess
import time
import unittest

import requests
import zaza.controller as controller
import zaza.model as model

TEST_TIMEOUT = 180
DEFAULT_API_PORT = "9177"
DEFAULT_API_URL = "/"
PACKAGES = ("qemu-kvm", "libvirt-daemon", "libvirt-daemon-system", "virtinst")
CIRROS_URL = "https://download.cirros-cloud.net/0.5.1/cirros-0.5.1-{}-disk.img"
UBUNTU_SERIES_CODE = {
    "jammy": "22.04",
    "focal": "20.04",
}
UBUNTU_BASE_SERIES_MAP = {
    "ubuntu@22.04": "jammy",
    "ubuntu@20.04": "focal",
}


def get_machine_series(machine):
    """Thin wrapper to ensure compatibility with juju 2 and 3."""
    series = ""
    try:
        series = machine.series
    except KeyError:
        series = UBUNTU_BASE_SERIES_MAP.get(machine.base)
    return series


class BasePrometheusLibvirtExporterTest(unittest.TestCase):
    """Base for Prometheus-libvirt-exporter charm tests."""

    @classmethod
    def setUpClass(cls):
        """Set up tests."""
        super(BasePrometheusLibvirtExporterTest, cls).setUpClass()
        cls.model_name = model.get_juju_model()
        cls.application_name = "prometheus-libvirt-exporter"
        cls.lead_unit_name = model.get_lead_unit_name(
            cls.application_name, model_name=cls.model_name
        )
        cls.units = model.get_units(cls.application_name, model_name=cls.model_name)
        model.block_until_all_units_idle()
        # workaround for 'Public address not found for prometheus-libvirt-exporter/0'
        # https://github.com/openstack-charmers/zaza/issues/472
        os.environ["ZAZA_FEATURE_BUG472"] = "1"
        cls.prometheus_libvirt_exporter_ip = model.get_app_ips(cls.application_name)[0]
        del os.environ["ZAZA_FEATURE_BUG472"]

        # Get the arch of the VM
        result = model.run_on_unit(cls.lead_unit_name, "uname -p")
        code = result.get("Code")
        if code != "0":
            raise model.CommandRunFailed("uname -p", result)
        cls.arch = result.get("Stdout", "").strip()

        # Ubuntu_ARM64_4C_16G_01 github runner does not support kvm, so we skip
        # the setting up vm here. If the workflow changes, please visit this
        # condition.
        if cls.arch == "aarch64":
            return

        if controller.get_cloud_type() == "lxd":
            # Get hostname
            logging.info(f"Getting hostname for unit {cls.lead_unit_name}")
            cmd = "hostname"
            result = model.run_on_unit(cls.lead_unit_name, cmd)
            code = result.get("Code")
            if code != "0":
                raise model.CommandRunFailed(cmd, result)
            hostname = result.get("Stdout").strip()

            # Set privileged container
            logging.info(f"Running cmd: 'lxc config set {hostname} " "security.privileged true'")
            privileged_cmd = f"lxc config set {hostname} security.privileged true"
            subprocess.call(privileged_cmd, shell=True)

            # Attach kvm device
            logging.info(
                f"Running cmd: 'lxc config device add {hostname} kvm unix-char path=/dev/kvm'"
            )
            kvm_cmd = f"lxc config device add {hostname} kvm unix-char path=/dev/kvm"
            subprocess.call(kvm_cmd, shell=True)
            # Restart container
            logging.info(f"Running cmd: 'lxc restart {hostname}'")
            restart_lxc = f"lxc restart {hostname}"
            subprocess.call(restart_lxc, shell=True)
            model.block_until_all_units_idle()

        # Set proxy on wget if present.
        wget_cmd = "sudo wget "

        https_proxy = os.getenv("HTTPS_PROXY")
        if https_proxy:
            wget_cmd += f"-e use_proxy=yes -e https_proxy='{https_proxy}' "

        wget_cmd += f"-q {CIRROS_URL} -O /var/lib/libvirt/images/cirros.img"

        wget_cmd = wget_cmd.format(result.get("Stdout").strip())

        # Install libvirt pkgs and bring up VM
        machine = model.get_machines(cls.application_name)[0]
        series = get_machine_series(machine)

        osinfo = ""
        if series == "jammy":
            osinfo = f"--osinfo ubuntu{UBUNTU_SERIES_CODE.get(series)}"

        cmd = """
        sudo apt-get update
        sudo apt-get -qy install {}
        {}
        sudo virt-install --name testvm --memory 128 \
          --cdrom /var/lib/libvirt/images/cirros.img \
          --nographics --nonetworks  --noautoconsole --nodisk \
          {}
        """.format(
            " ".join(PACKAGES), wget_cmd, osinfo
        )
        result = model.run_on_unit(cls.lead_unit_name, cmd)
        code = result.get("Code")
        if code != "0":
            raise model.CommandRunFailed(cmd, result)

    @classmethod
    def tearDownClass(cls):
        """Destroy test resources."""
        cmd = "sudo virsh destroy testvm ; sudo virsh undefine testvm"
        model.run_on_unit(cls.lead_unit_name, cmd)


class CharmOperationTest(BasePrometheusLibvirtExporterTest):
    """Verify operations."""

    def test_01_api_ready(self):
        """Verify if the API is ready.

        Curl the api endpoint.
        We'll retry until the CURL_TIMEOUT.
        """
        curl_command = f"curl http://localhost:{DEFAULT_API_PORT}/metrics"
        timeout = time.time() + TEST_TIMEOUT
        while time.time() < timeout:
            response = model.run_on_unit(self.lead_unit_name, curl_command)
            if response["Code"] == "0":
                return
            logging.warning(f"Unexpected curl response: {response}. Retrying in 30s.")
            time.sleep(30)

        # we didn't get rc=0 in the allowed time, fail the test
        self.fail(
            "Prometheus-libvirt-exporter didn't respond to the command \n"
            f"'{curl_command}' as expected.\n"
            f"Result: {response}"
        )

    def test_02_api_metrics(self):
        """Verify if we get libvirt metrics from the scrape endpoint."""
        timeout = time.time() + TEST_TIMEOUT
        url = f"http://{self.prometheus_libvirt_exporter_ip}:{DEFAULT_API_PORT}/metrics"
        expected_machine_count = 1 if self.arch == "x86_64" else 0
        while time.time() < timeout:
            response = requests.get(url)

            if response.status_code == 200:
                metrics = [
                    line for line in response.text.splitlines() if line.startswith("libvirt")
                ]
                self.assertTrue(f"libvirt_up {expected_machine_count}" in metrics)
                pat = re.compile(r"libvirt_domain_info_virtual_cpus.*testvm")
                matches = [metric for metric in metrics if pat.search(metric)]
                self.assertEqual(len(matches), expected_machine_count)
                return

            logging.warning(
                f"Unexpected GET response. Response Code: {response.status_code}. Retrying in 30s."
            )
            time.sleep(30)

        self.fail(
            "Prometheus-libvirt-exporter didn't respond to the get request to \n"
            f"'{url}' as expected.\n"
            f"Response code: {response.status_code}, Text: {response.text}"
        )
