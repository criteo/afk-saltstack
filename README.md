# Saltstack Openconfig module

> This repository is part of [AFK](https://criteo.github.io/AFK)

## Context

This repo contains our Saltstack codebase necessary to apply configuration on network devices using configuration inputs in OpenConfig.

The full documentation can be found here: [AFK documentation](https://criteo.github.io/AFK/SaltStack-modules/installation/)

## Be careful

These modules are under active development and are subject to changes.

The implementation is opiniated and might not be appropriate for your environment.

You should always test new releases on your infrastructure before going to production.

Criteo cannot be held responsible for incidents in your infrastructure.

## Deprecated: peer-groups

Peer Groups are temporarily supported for migration.

We have decided to remove peer-group support to simplify the modules and the template. It will also remove risks associated with changes in peer groups.

## What is it?

This repository contains all the necessary modules to apply OpenConfig to network devices. It uses templates to convert OpenConfig to configuration/commands.

It does not aim to cover 100% of OpenConfig model.

Supported Network OS:
- [SONiC](https://github.com/sonic-net/SONiC)
- Juniper JunOS
- Arista EOS

## How to install

The recommended configuration is to download the modules in this repo to a dedicated path on your Salt-master.

Example of salt-master configuration:
```yaml
file_roots:
  base:
    - /srv/salt/base/your-base/   # your own code base
    - /srv/salt/base/openconfig/  # openconfig code base
    - /srv/salt/base/sonic/       # if you want SONiC support: https://github.com/criteo/sonic-saltstack
```

## How to use

* Dry run: `salt <device> state.apply full_config test=True`
* Deploy: `salt <device> state.apply full_config`

## Dependencies

Depending on the Network OS you want to support, you will need:

- [SONiC modules](https://github.com/criteo/sonic-saltstack)
- [napalm-salt](https://github.com/napalm-automation/napalm-salt) for Juniper JunOS and Arista EOS

## How to contribute

see [CONTRIBUTING.md](CONTRIBUTING.md)
