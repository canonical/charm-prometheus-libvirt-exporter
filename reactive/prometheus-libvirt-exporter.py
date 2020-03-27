#!/usr/bin/python3
"""Installs and configures prometheus-libvirt-exporter."""

import os
from pathlib import Path
import shutil
import subprocess
from zipfile import BadZipFile, ZipFile

from charmhelpers.contrib.charmsupport import nrpe
from charmhelpers.core import hookenv, host
from charms.layer import snap
from charms.reactive import (
    endpoint_from_flag,
    hook,
    remove_state,
    set_state,
    when,
    when_all,
    when_any,
    when_not,
    when_not_all
)


DASHBOARD_PATH = os.getcwd() + '/files/grafana-dashboards'
SNAP_NAME = 'prometheus-libvirt-exporter'
SVC_NAME = 'snap.prometheus-libvirt-exporter.daemon'
PORT_NUMBER = '9177'


@when('juju-info.connected')
@when_not_all('libvirt-exporter.installed', 'libvirt-exporter.started')
def install_packages():
    """Installs the prometheus-libvirt-exporter snap."""
    hookenv.status_set('maintenance', 'Installing software')
    config = hookenv.config()
    channel = config.get('snap_channel')
    snap.install(SNAP_NAME, channel=channel, force_dangerous=False)
    subprocess.check_call(['snap', 'connect', 'prometheus-libvirt-exporter:libvirt'])
    hookenv.status_set('active', 'Exporter installed and connected to libvirt slot')
    hookenv.open_port(PORT_NUMBER)
    set_state('libvirt-exporter.installed')


@hook('upgrade-charm')
def upgrade():
    """Reset the install state on upgrade, to ensure resource extraction."""
    hookenv.status_set('maintenance', 'Charm upgrade in progress')
    remove_state('libvirt-exporter.installed')
    remove_state('libvirt-exporter.started')
    update_dashboards_from_resource()


@when_not('libvirt-exporter.started')
@when_any('libvirt-exporter.installed', 'config.changed')
def start_snap():
    """Configure snap.prometheus-libvirt-exporter.daemon service."""
    if not host.service_running(SVC_NAME):
        hookenv.status_set('maintenance', 'Service is down, starting')
        hookenv.log('Service {} is down, starting...'.format(SVC_NAME))
        host.service_start(SVC_NAME)
        hookenv.status_set('active', 'Service started')
        hookenv.log('start_snap() Service started')
    else:
        hookenv.status_set('active', 'Ready')
        set_state('libvirt-exporter.started')
        hookenv.log('start_snap() libvirt-exporter.started')

    update_dashboards_from_resource()

    hookenv.log('Installed and set flag libvirt-exporter.started')


@when('config.changed.snap_channel')
def snap_channel_changed():
    """Remove the state libvirt.exporter.installed if the snap channel changes."""
    remove_state('libvirt-exporter.installed')
    remove_state('libvirt-exporter.started')


@when_all('libvirt-exporter.started', 'scrape.available')
def configure_scrape_relation(scrape_service):
    """Connect prometheus to the the exporter for consumption."""
    scrape_service.configure(PORT_NUMBER)
    remove_state('libvirt-exporter.configured')


@when('nrpe-external-master.changed')
def nrpe_changed():
    """Trigger nrpe update."""
    remove_state('libvirt-exporter.configured')


@when('libvirt-exporter.changed')
def prometheus_changed():
    """Trigger prometheus update."""
    remove_state('libvirt-exporter.prometheus_relation_configured')
    remove_state('libvirt-exporter.configured')


@when('nrpe-external-master.available')
@when_not('libvirt-exporter.configured')
def update_nrpe_config(svc):
    """Configure the nrpe check for the service."""
    if not os.path.exists('/var/lib/nagios'):
        hookenv.status_set('blocked', 'Waiting for nrpe package installation')
        return

    hookenv.status_set('maintenance', 'Configuring nrpe checks')

    hostname = nrpe.get_nagios_hostname()
    nrpe_setup = nrpe.NRPE(hostname=hostname)
    nrpe_setup.add_check(shortname='prometheus_libvirt_exporter_http',
                         check_cmd='check_http -I 127.0.0.1 -p {} -u /metrics'.format(PORT_NUMBER),
                         description='Prometheus Libvirt Exporter HTTP check')
    nrpe_setup.write()
    hookenv.status_set('active', 'ready')
    set_state('libvirt-exporter.configured')


@when('libvirt-exporter.installed')
@when_not('juju-info.available')
def remove_libvirt_exporter():
    """Uninstall the snap."""
    remove_state('libvirt-exporter.installed')
    remove_state('libvirt-exporter.started')
    snap.remove(SNAP_NAME)


@when('libvirt-exporter.configured')
@when_not('nrpe-external-master.available')
def remove_nrpe_check():
    """Remove the nrpe check."""
    hostname = nrpe.get_nagios_hostname()
    nrpe_setup = nrpe.NRPE(hostname=hostname)
    nrpe_setup.remove_check(shortname="prometheus_libvirt_exporter_http")
    remove_state('libvirt-exporter.configured')


@when_all('leadership.is_leader', 'endpoint.dashboards.joined')
def register_grafana_dashboards():
    """After joining to grafana, push the dashboard."""
    grafana_endpoint = endpoint_from_flag('endpoint.dashboards.joined')

    if grafana_endpoint is None:
        return

    hookenv.log('Grafana relation joined, push dashboard')

    # load pre-distributed dashboards, that may have been overwritten by resource
    dash_dir = Path(DASHBOARD_PATH)
    for dash_file in dash_dir.glob('*.json'):
        dashboard = dash_file.read_text()
        grafana_endpoint.register_dashboard(dash_file.stem, dashboard)
        hookenv.log('Pushed {}'.format(dash_file))


def update_dashboards_from_resource():
    """Extract resource zip file into templates directory."""
    dashboards_zip_resource = hookenv.resource_get('dashboards')
    if not dashboards_zip_resource:
        hookenv.log('No dashboards resource found', hookenv.DEBUG)
        # no dashboards zip found, go with the default distributed dashboard
        return

    hookenv.log('Installing dashboards from resource', hookenv.DEBUG)
    try:
        shutil.copy(dashboards_zip_resource, DASHBOARD_PATH)
    except IOError as error:
        hookenv.log('Problem copying resource: {}'.format(error), hookenv.ERROR)
        return

    try:
        with ZipFile(dashboards_zip_resource, 'r') as zipfile:
            zipfile.extractall(path=DASHBOARD_PATH)
            hookenv.log('Extracted dashboards from resource', hookenv.DEBUG)
    except BadZipFile as error:
        hookenv.log('BadZipFile: {}'.format(error), hookenv.ERROR)
        return
    except PermissionError as error:
        hookenv.log('Unable to unzip the provided resource: {}'.format(error), hookenv.ERROR)
        return

    register_grafana_dashboards()
