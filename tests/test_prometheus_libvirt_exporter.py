"""Encapsulate prometheus-libvirt-exporter testing."""
import logging
import re
import time
import unittest

import requests
import zaza.model as model


CURL_TIMEOUT = 180
REQ_TIMEOUT = 12
DEFAULT_API_PORT = "9177"
DEFAULT_API_URL = "/metrics"
PACKAGES = ("libvirt-clients", "libvirt-daemon", "libvirt-daemon-system",
            "virtinst")
CIRROS_URL = "https://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img"


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
        cls.units = model.get_units(
            cls.application_name, model_name=cls.model_name
        )
        cls.prometheus_libvirt_exporter_ip = model.get_app_ips(cls.application_name)[0]
        model.block_until_all_units_idle()
        # Install libvirt pkgs and bring up VM
        cmd = """
        sudo apt-get update
        sudo apt-get -qy install {}
        sudo wget -q {} -O /var/lib/libvirt/images/cirros.img
        sudo virt-install --name testvm --memory 128 \
          --cdrom /var/lib/libvirt/images/cirros.img \
          --nographics --nonetworks  --noautoconsole --nodisk
        """.format(" ".join(PACKAGES), CIRROS_URL)
        result = model.run_on_unit(cls.lead_unit_name, cmd)
        code = result.get('Code')
        if code != '0':
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
        curl_command = "curl http://localhost:{}/metrics".format(DEFAULT_API_PORT)
        timeout = time.time() + CURL_TIMEOUT
        while time.time() < timeout:
            response = model.run_on_unit(self.lead_unit_name, curl_command)
            if response["Code"] == "0":
                return
            logging.warning(
                "Unexpected curl response: {}. Retrying in 30s.".format(
                    response
                )
            )
            time.sleep(30)

        # we didn't get rc=0 in the allowed time, fail the test
        self.fail(
            "Prometheus-libvirt-exporter didn't respond to the command \n"
            "'{curl_command}' as expected.\n"
            "Result: {result}".format(
                curl_command=curl_command, result=response
            )
        )

    def test_02_nrpe_http_check(self):
        """Verify nrpe check exists."""
        expected_nrpe_check = "command[check_prometheus_libvirt_exporter_http]={} -I 127.0.0.1 -p {} -u {}".format(
            "/usr/lib/nagios/plugins/check_http",
            DEFAULT_API_PORT,
            DEFAULT_API_URL
        )
        logging.debug('Verify the nrpe check is created and has the required content...')
        cmd = "cat /etc/nagios/nrpe.d/check_prometheus_libvirt_exporter_http.cfg"
        result = model.run_on_unit(self.lead_unit_name, cmd)
        code = result.get('Code')
        if code != '0':
            raise model.CommandRunFailed(cmd, result)
        content = result.get('Stdout')
        self.assertTrue(expected_nrpe_check in content)

    def test_05_api_metrics(self):
        """Verify if we get libvirt metrics from the scrape endpoint."""
        response = requests.get("http://{}:{}/metrics".format(
            self.prometheus_libvirt_exporter_ip, DEFAULT_API_PORT)
        )
        metrics = [line for line in response.text.splitlines() if line.startswith("libvirt")]
        self.assertTrue("libvirt_up 1" in metrics)
        pat = re.compile(r'libvirt_domain_info_virtual_cpus.*testvm')
        matches = [metric for metric in metrics if pat.search(metric)]
        self.assertEqual(len(matches), 1)
