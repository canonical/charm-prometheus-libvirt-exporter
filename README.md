# Juju prometheus libvirt exporter charm

This charm provides the [Prometheus libvirt exporter](https://github.com/Tinkoff/libvirt-exporter) (via the [snap](https://snapcraft.io/prometheus-libvirt-exporter)).

## Deployment

A typical deployment with nova and libvirt is as follows:

(The metrics will be at http://nova-compute:9177)

```
juju deploy nova-compute
juju deploy prometheus-libvirt-exporter
juju add-relation nova-compute prometheus-libvirt-exporter
```

To avail of the metrics in grafana the following steps can be used:

```
juju deploy grafana
juju deploy prometheus2
juju add-relation prometheus-libvirt-exporter:scrape prometheus2:target
juju add-relation prometheus-libvirt-exporter:dashboards grafana:dashboards
```

To setup reporting with nagios:

```
juju deploy nrpe
juju add-relation nova-compute nrpe
juju add-relation prometheus-libvirt-exporter:nrpe-external-master nrpe:nrpe-external-master
```

To change or update dashboards:

```
# The exporter is distributed with a standard dashboard
# To provide your own dashboards, create a zip file and attach it as a resource
zip grafana-dashboards.zip libvirt-simple.json libvirtadvanced.json
juju attach-resource prometheus-libvirt-exporter dashboards=./grafana-dashboards.zip
```

## Testing

This directory needs to be create in the charm path prior to testing

```
mkdir -p report/lint
```

### Functional tests

Juju should be installed and bootstrapped on the system to run functional tests.

```
export HTTPS_PROXY=http://<your_proxy
export NO_PROXY=127.0.0.1,localhost,<juju_controller_ips>
export MODEL_SETTINGS=<semicolon-separated list of "juju model-config" settings>
make test
```

NOTE: If you are behind a proxy, be sure to export a MODEL_SETTINGS variable as
described above. Note that you will need to use the juju-http-proxy,
juju-https-proxy, juju-no-proxy and similar settings. Also you will need to
export HTTPS_PROXY used in the test and export NO_PROXY that should include ips
of controller subnet and model subnet.

## List of metrics collected by prometheus-libvirt-exporter snap

See [List of metrics](./metrics.md)

# Contact Information
- Charm bugs: https://github.com/canonical/charm-prometheus-libvirt-exporter/issues
