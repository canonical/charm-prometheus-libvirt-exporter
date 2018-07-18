from charmhelpers.core import hookenv, host
from charms.reactive import (
    when, when_not, set_state, remove_state
)
from charms.layer import snap


SNAP_NAME = 'prometheus-libvirt-exporter'
SVC_NAME = 'snap.prometheus-libvirt-exporter.daemon'
PORT_NUMBER = '9177'


@when_not('libvirt-exporter.installed')
def install_packages():
    hookenv.status_set('maintenance', 'Installing software')
    config = hookenv.config()
    channel = config.get('snap_channel', 'stable')
    snap.install(SNAP_NAME, channel=channel, force_dangerous=False)
    hookenv.status_set('active', 'Exporter installed without problems')
    hookenv.open_port(PORT_NUMBER)
    set_state('libvirt-exporter.installed')


@when('libvirt-exporter.installed')
def check_status():
    config = hookenv.config()
    if config.changed('snap_channel'):
        remove_state('libvirt-exporter.installed')
        return
    if not host.service_running(SVC_NAME):
        hookenv.status_set('maintenance', 'Service is down, starting')
        hookenv.log('Service {} is down, starting...'.format(SVC_NAME))
        host.service_start(SVC_NAME)
        hookenv.status_set('active', 'Service started')
    else:
        hookenv.status_set('active', 'Service is up')
        set_state('libvirt-exporter.started')


# Relations
@when('libvirt-exporter.started')
@when('scrape.available')
def configure_scrape_relation(scrape_service):
    scrape_service.configure(PORT_NUMBER)
