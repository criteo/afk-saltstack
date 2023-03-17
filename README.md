# Saltstack Openconfig module

> This repository is part of [Criteo AFK](https://github.com/criteo/criteo-network-automation-stack)

## Context

This repo contains our Saltstack codebase necessary to apply configuration on network devices using configuration inputs in OpenConfig.

## Be careful

These modules are under active development and is subject to changes.

The implementation is opiniated and might not be appropriate for your environment.

You should always test new releases on your infrastructure before going to production.

Criteo cannot be held responsible for incident in your infrastructure.

## Deprecated: peer-groups

Please be informed that peer-groups are currently support only during transition window. We have decided to remove peer-group support to simplify the modules and the template. It will also remove risks associated to changes on peer-group.

More info to come in the FAQ...

## What it is?

This repository contains all the code necessary to apply OpenConfig to network devices. It uses templates to convert OpenConfig to configuration/commands.

It does not aim to cover 100% of OpenConfig model.

Supported Network OS:
- [SONiC](https://github.com/sonic-net/SONiC)
- Juniper JunOS
- Arista EOS

Supported modules:
- BGP
- Routing policy

Coming support:
- BGP EVPN
- VXLAN type 5
- Interfaces
- Syslog
- SNMP
- TACACS (to be confirmed)
- Users (to be confirmed)

## How to install

The recommended configuration is to download the code in this repo to a dedicated path on your Salt-master.

Example of salt-master configuration:
```yaml
file_roots:
  base:
    - /srv/salt/base/your-base/   # your own code base
    - /srv/salt/base/openconfig/  # openconfig code base
    - /srv/salt/base/sonic/       # if you want SONiC support: https://github.com/criteo/sonic-saltstack
```

## How to use

* Dry-run: `salt <device> state.apply full_config test=True`
* Deploy: `salt <device> state.apply full_config`

TODO: complete the documentation...

## Dependencies

Depending on the Network OS you want to support, you will need:
- [SONiC modules](https://github.com/criteo/sonic-saltstack)
- [napalm-salt](https://github.com/napalm-automation/napalm-salt) for Juniper JunOS and Arista EOS

## How to contribute

see [CONTRIBUTING.md](CONTRIBUTING.md)
