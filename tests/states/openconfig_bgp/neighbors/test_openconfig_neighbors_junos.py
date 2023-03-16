"""Unit test openconfig_bgp peer-group."""

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("junos")
def test__generate_neighbor_part__minimal_ipv4_up(mocker):
    """Test neighbor with minimal configuration in IPv4."""
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

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(config, 65000, {}, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 peer-as 65001\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 local-as\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT preference 20\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 description \"my_neighbor\"\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 authentication-key\n"
        "activate routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast\n"
            "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast prefix-limit"
        ),
        "IPV6_UNICAST": (
            "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet6 unicast"
        ),
    }


@salt_bgp_mock("junos")
def test__generate_neighbor_part__minimal_ipv4_shutdown_different_local_as(mocker):
    """Test neighbor with minimal configuration in IPv4.

    Session shutdown, different local as than the global as.
    """
    config = {
        "neighbor-address": "192.0.2.1",
        "config": {
            "peer-group": "PG-DEFAULT",
            "neighbor-address": "192.0.2.1",
            "enabled": False,
            "peer-as": 65001,
            "local-as": 65002,
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

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(config, 65000, {}, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 peer-as 65001\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 local-as 65002\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT preference 20\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 description \"my_neighbor\"\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 authentication-key\n"
        "deactivate routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast\n"
            "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast prefix-limit"
        ),
        "IPV6_UNICAST": (
            "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet6 unicast"
        ),
    }


@salt_bgp_mock("junos")
def test__generate_neighbor_part__minimal_ipv4_with_route_maps(mocker):
    """Test neighbor with minimal configuration in IPv4 with route-maps."""
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
        "apply-policy": {"config": {"import-policy": ["RM-1-IN"], "export-policy": ["RM-1-OUT"]}},
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

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(config, 65000, {}, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 peer-as 65001\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 local-as\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT preference 20\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 description \"my_neighbor\"\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 authentication-key\n"
        "activate routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast\n"
            "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast prefix-limit\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import [RM-1-IN]\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export [RM-1-OUT]"
        ),
        "IPV6_UNICAST": (
            "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet6 unicast"
        ),
    }

@salt_bgp_mock("junos")
def test__generate_neighbor_part__minimal_ipv6(mocker):
    """Test neighbor with minimal configuration in IPv6."""
    config = {
        "neighbor-address": "2001:db8::1",
        "config": {
            "peer-group": "PG-TOR",
            "neighbor-address": "2001:db8::1",
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
                    "afi-safi-name": "IPV6_UNICAST",
                    "config": {"afi-safi-name": "IPV6_UNICAST", "enabled": False},
                    "apply-policy": {"config": {"import-policy": [], "export-policy": []}},
                    "ipv6-unicast": {"prefix-limit": {"config": {"max-prefixes": 0}}},
                }
            ]
        },
    }

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(config, 65000, {}, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 peer-as 65001\n"
        "delete routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 local-as\n"
        "set routing-instances prod protocols bgp group PG-TOR preference 20\n"
        "set routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 description \"my_neighbor\"\n"
        "delete routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 authentication-key\n"
        "activate routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1\n"
        "delete routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 import\n"
        "delete routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 export"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "delete routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 family inet unicast"
        ),
        "IPV6_UNICAST": (
            "delete routing-instances prod protocols bgp group PG-TOR neighbor 2001:db8::1 family inet6 unicast"
        ),
    }


@salt_bgp_mock("junos")
def test__generate_neighbor_part__full(mocker):
    """Test neighbor with full configuration."""
    config = {
        "neighbor-address": "192.0.2.1",
        "config": {
            "peer-group": "PG-DEFAULT",
            "neighbor-address": "192.0.2.1",
            "enabled": True,
            "peer-as": 65001,
            "local-as": 65002,
            "auth-password": "thisisasecret",
            "description": "my_neighbor",
            "peer-type": None,
            "remove-private-as": None,
            "send-community": "NONE",
        },
        "apply-policy": {"config": {"import-policy": ["RM-1-IN"], "export-policy": ["RM-1-OUT"]}},
        "afi-safis": {
            "afi-safi": [
                {
                    "afi-safi-name": "IPV4_UNICAST",
                    "config": {"afi-safi-name": "IPV4_UNICAST", "enabled": True},
                    "apply-policy": {
                        "config": {"import-policy": ["RM-2-IN"], "export-policy": ["RM-2-OUT"]}
                    },
                    "ipv4-unicast": {"prefix-limit": {"config": {"max-prefixes": 1000}}},
                },
                {
                    "afi-safi-name": "IPV6_UNICAST",
                    "config": {"afi-safi-name": "IPV6_UNICAST", "enabled": True},
                    "apply-policy": {"config": {"import-policy": [], "export-policy": []}},
                    "ipv6-unicast": {"prefix-limit": {"config": {"max-prefixes": 1000}}},
                },
            ]
        },
    }
    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(config, 65000, {}, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 peer-as 65001\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 local-as 65002\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT preference 20\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 description \"my_neighbor\"\n"
        "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 authentication-key thisisasecret\n"
        "activate routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import\n"
        "delete routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet unicast prefix-limit maximum 1000\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import [AUTOGENERATED::RM-2-IN::IPV4_UNICAST]\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export [AUTOGENERATED::RM-2-OUT::IPV4_UNICAST]"
        ),
        "IPV6_UNICAST": (
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet6 unicast\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 family inet6 unicast prefix-limit maximum 1000\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 import [RM-1-IN]\n"
            "set routing-instances prod protocols bgp group PG-DEFAULT neighbor 192.0.2.1 export [RM-1-OUT]"
        ),
    }


@salt_bgp_mock("junos")
def test__generate_neighbor_part__exists_in_another_pg(mocker):
    """Test neighbor with minimal configuration in IPv4 but already exists in another PG."""
    config = {
        "neighbor-address": "192.0.2.2",
        "config": {
            "peer-group": "NEW-PG",
            "neighbor-address": "192.0.2.2",
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

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(config, 65000, {}, None)
    assert neighbor_config == (
        "set routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 peer-as 65001\n"
        "delete routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 local-as\n"
        "set routing-instances prod protocols bgp group NEW-PG preference 20\n"
        "set routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 description \"my_neighbor\"\n"
        "delete routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 authentication-key\n"
        "activate routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2\n"
        "delete routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 import\n"
        "delete routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 export"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "set routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 family inet unicast\n"
            "delete routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 family inet unicast prefix-limit"
        ),
        "IPV6_UNICAST": (
            "delete routing-instances prod protocols bgp group NEW-PG neighbor 192.0.2.2 family inet6 unicast"
        ),
    }
