"""Unit test openconfig_bgp peer-group."""
import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("junos")
def test__generate_peer_group_part__minimal(mocker):
    """Test peer-group with no specific configuration."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {
            "local-as": None,
            "peer-as": 65000,
            "description": "",
        },
        "apply-policy": {},
        "afi-safis": {},
    }
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR local-as\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR peer-as 65000\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR preference\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR description\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR import\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR export"
    )

    assert safi_config == {
        "IPV4_UNICAST": "delete routing-instances prod protocols bgp group RA02.01:PG-TOR family inet unicast",
        "IPV6_UNICAST": "delete routing-instances prod protocols bgp group RA02.01:PG-TOR family inet6 unicast",
    }


@salt_bgp_mock("junos")
def test__generate_peer_group_part__simple(mocker):
    """Test peer-group with simple configuration: no SAFI."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {"local-as": 60000, "peer-as": 60001, "description": "L3_RA"},
        "apply-policy": {
            "config": {"import-policy": ["RM-LAN-IN"], "export-policy": ["RM-LAN-OUT"]}
        },
        "afi-safis": {},
    }

    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR local-as 60000\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR peer-as 60001\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR preference 20\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR description \"L3_RA\"\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR import\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR import [RM-LAN-IN]\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR export\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR export [RM-LAN-OUT]"
    )

    assert safi_config == {
        "IPV4_UNICAST": "delete routing-instances prod protocols bgp group RA02.01:PG-TOR family inet unicast",
        "IPV6_UNICAST": "delete routing-instances prod protocols bgp group RA02.01:PG-TOR family inet6 unicast",
    }


@salt_bgp_mock("junos")
def test__generate_peer_group_part_with_safi(mocker):
    """Test peer-group with safi."""
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

    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR local-as 60000\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR peer-as 65001\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR preference 20\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR description \"L3_RA\"\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR import\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR import [RM-LAN-IN]\n"
        "delete routing-instances prod protocols bgp group RA02.01:PG-TOR export\n"
        "set routing-instances prod protocols bgp group RA02.01:PG-TOR export [RM-LAN-OUT]"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "set routing-instances prod protocols bgp group RA02.01:PG-TOR family inet unicast\n"
            "set routing-instances prod protocols bgp group RA02.01:PG-TOR family inet unicast prefix-limit maximum 10000\n"
            "set routing-instances prod protocols bgp group RA02.01:PG-TOR import [RM-LAN-IN]\n"
            "set routing-instances prod protocols bgp group RA02.01:PG-TOR export [RM-LAN-OUT]"
        ),
        "IPV6_UNICAST": "delete routing-instances prod protocols bgp group RA02.01:PG-TOR family inet6 unicast",
    }
