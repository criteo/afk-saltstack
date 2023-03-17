"""Unit test openconfig_bgp global configuration."""

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("junos")
def test__generate_global_configuration_minimal(mocker):
    config = {
        "config": {"as": 65000},
    }
    assert (
        STATE_MOD._generate_global_conf_part(config, None)
        == "set routing-instances prod protocols bgp multipath multiple-as"
    )


@salt_bgp_mock("junos")
def test__generate_global_configuration_minimal2(mocker):
    config = {
        "config": {"as": 65000},
        "default-route-distance": {"config": {"external-route-distance": 20}},
        "graceful-restart": {
            "config": {"enabled": True},
        },
    }
    assert STATE_MOD._generate_global_conf_part(config, None) == (
        "set routing-instances prod protocols bgp multipath multiple-as\n"
        "set routing-instances prod protocols bgp graceful-restart\n"
        "delete routing-instances prod protocols bgp graceful-restart restart-time"
    )


@salt_bgp_mock("junos")
def test__generate_global_configuration_full(mocker):
    config = {
        "config": {"as": 65000, "router-id": "127.0.0.1"},
        "default-route-distance": {
            "config": {"external-route-distance": 20, "internal-route-distance": 170}
        },
        "graceful-restart": {"config": {"enabled": True, "restart-time": 240}},
        "use-multiple-paths": {
            "config": {"enabled": True},
            "ebgp": {"config": {"maximum-paths": 128}},
            "ibgp": {"config": {"maximum-paths": 128}},
        },
    }
    assert STATE_MOD._generate_global_conf_part(config, None) == (
        "set routing-instances prod protocols bgp multipath multiple-as\n"
        "set routing-instances prod protocols bgp graceful-restart\n"
        "set routing-instances prod protocols bgp graceful-restart restart-time 240"
    )


##
# ECMP tests: in JunOS, maximum-path option cannot be set globally, but can be per neighbor/group
##


@salt_bgp_mock("junos")
def test__generate_global_configuration_ecmp_neighbors_ebgp(mocker):
    """Test neighbor with ecmp enabled."""
    config = {
        "neighbor-address": "192.0.2.1",
        "config": {
            "peer-group": "PG-DEFAULT",
            "neighbor-address": "192.0.2.1",
            "enabled": True,
            "peer-as": 65001,
            "local-as": 65000,
            "auth-password": "",
            "description": "my_neighbor",
            "peer-type": None,
            "remove-private-as": None,
            "send-community": "NONE",
        },
        "apply-policy": {"config": {"import-policy": [], "export-policy": []}},
        "afi-safis": {
            "afi-safi": [
                {
                    "afi-safi-name": "IPV4_UNICAST",
                    "config": {"afi-safi-name": "IPV4_UNICAST", "enabled": True},
                    "apply-policy": {"config": {"import-policy": [], "export-policy": []}},
                    "ipv4-unicast": {"prefix-limit": {"config": {"max-prefixes": 0}}},
                }
            ]
        },
    }
    bgp_distance = {
        "external": 50,
        "internal": 150,
    }
    neighbor_config, _ = STATE_MOD._generate_neighbor_config(config, 65000, bgp_distance, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 peer-as 65001\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 local-as\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT preference 50\n"
        'set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 description "my_neighbor"\n'
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 authentication-key\n"
        "activate routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export"
    )


@salt_bgp_mock("junos")
def test__generate_global_configuration_ecmp_neighbors_ibgp(mocker):
    """Test neighbor with ecmp enabled."""
    config = {
        "neighbor-address": "192.0.2.1",
        "config": {
            "peer-group": "PG-DEFAULT",
            "neighbor-address": "192.0.2.1",
            "enabled": True,
            "peer-as": 65000,
            "local-as": 65000,
            "auth-password": "",
            "description": "my_neighbor",
            "peer-type": None,
            "remove-private-as": None,
            "send-community": "NONE",
        },
        "apply-policy": {"config": {"import-policy": [], "export-policy": []}},
        "afi-safis": {
            "afi-safi": [
                {
                    "afi-safi-name": "IPV4_UNICAST",
                    "config": {"afi-safi-name": "IPV4_UNICAST", "enabled": True},
                    "apply-policy": {"config": {"import-policy": [], "export-policy": []}},
                    "ipv4-unicast": {"prefix-limit": {"config": {"max-prefixes": 0}}},
                }
            ]
        },
    }
    bgp_distance = {
        "external": 50,
        "internal": 150,
    }

    neighbor_config, _ = STATE_MOD._generate_neighbor_config(config, 65000, bgp_distance, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 peer-as 65000\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 local-as\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT preference 150\n"
        'set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 description "my_neighbor"\n'
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 authentication-key\n"
        "activate routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export"
    )


@salt_bgp_mock("junos")
def test__generate_global_configuration_ecmp_peer_groups_ebgp(mocker):
    """Test neighbor with ecmp enabled."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {"local-as": 60000, "peer-as": 65001, "description": "L3_RA"},
        "apply-policy": {
            "config": {"import-policy": ["RM-LAN-IN"], "export-policy": ["RM-LAN-OUT"]}
        },
        "afi-safis": {
            "afi-safi": [
                {
                    "afi-safi-name": "IPV4_UNICAST",
                    "config": {"afi-safi-name": "IPV4_UNICAST", "enabled": True},
                    "apply-policy": {},
                    "ipv4-unicast": {"prefix-limit": {"config": {"max-prefixes": 10000}}},
                }
            ]
        },
    }
    bgp_distance = {
        "external": 50,
        "internal": 150,
    }

    pg_config, _ = STATE_MOD._generate_peer_group(config, bgp_distance, None)
    assert pg_config == (
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR local-as 60000\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR peer-as 65001\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR preference 50\n"
        'set routing-instances prod protocols bgp group RA02.01:PG-TOR description "L3_RA"\n'
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR import\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR import [RM-LAN-IN]\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR export\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR export [RM-LAN-OUT]"
    )


@salt_bgp_mock("junos")
def test__generate_global_configuration_ecmp_peer_groups_ibgp(mocker):
    """Test peer groups with ecmp enabled."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {"local-as": 65000, "peer-as": 65000, "description": "L3_RA"},
        "apply-policy": {
            "config": {"import-policy": ["RM-LAN-IN"], "export-policy": ["RM-LAN-OUT"]}
        },
        "afi-safis": {
            "afi-safi": [
                {
                    "afi-safi-name": "IPV4_UNICAST",
                    "config": {"afi-safi-name": "IPV4_UNICAST", "enabled": True},
                    "apply-policy": {},
                    "ipv4-unicast": {"prefix-limit": {"config": {"max-prefixes": 10000}}},
                }
            ]
        },
    }
    bgp_distance = {
        "external": 50,
        "internal": 150,
    }

    pg_config, _ = STATE_MOD._generate_peer_group(config, bgp_distance, None)
    assert pg_config == (
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR local-as 65000\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR peer-as 65000\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR preference 150\n"
        'set routing-instances prod protocols bgp group RA02.01:PG-TOR description "L3_RA"\n'
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR import\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR import [RM-LAN-IN]\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR export\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR export [RM-LAN-OUT]"
    )
