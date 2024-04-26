# Contributing

## Developing

Fork the [repository](https://github.com/canonical/charm-prometheus-libvirt-exporter/),
and make some changes.

## Testing

```shell
make black          # reformat the code
make lint           # run lint tests
make unittests      # run unit tests
make functional     # run functional tests
make test           # run the complete test suite (lint, unit, functional tests)
```

## Build Charm

To build the charm locally:

```
make build
```
