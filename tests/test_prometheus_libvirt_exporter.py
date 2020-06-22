"""Encapsulate prometheus-libvirt-exporter testing."""
import logging
import time
import unittest

import requests
import zaza.model as model


CURL_TIMEOUT = 180
REQ_TIMEOUT = 12
DEFAULT_API_PORT = "9177"
DEFAULT_API_URL = "/metrics"


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

    def test_05_grafana_dashboard(self):
        """Test if the grafana dashboard was successfully registered."""
        action = model.run_action_on_leader("grafana", "get-admin-password")
        self.assertTrue(action.data["results"]["Code"] == "0")
        passwd = action.data["results"]["password"]
        grafana_ip = model.get_app_ips("grafana")[0]
        dash_url = "http://{}:3000/api/search".format(grafana_ip)
        headers = {"Content-Type": "application/json"}
        params = {"type": "dash-db", "query": "libvirt"}
        api_auth = ("admin", passwd)
        r = requests.get(dash_url, auth=api_auth, headers=headers, params=params)
        self.assertEqual(r.status_code, 200)
        dash = [d for d in r.json() if "Libvirt" in d["title"]]
        self.assertEqual(len(dash), 1)
