"""Unit test openconfig_bgp peer-group."""

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("eos")
def test__generate_peer_group_part__minimal_before_4_22(mocker):
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

    mocker.patch("_states.openconfig_bgp._get_eos_version", return_value=(4, 17))
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer-group\n"
        "default neighbor RA02.01:PG-TOR local-as\n"
        "neighbor RA02.01:PG-TOR remote-as 65000\n"
        "default neighbor RA02.01:PG-TOR description\n"
        "default neighbor RA02.01:PG-TOR route-map in\n"
        "default neighbor RA02.01:PG-TOR route-map out\n"
        "default neighbor RA02.01:PG-TOR maximum-routes\n"
        "neighbor RA02.01:PG-TOR send-community"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
        "IPV6_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
    }


@salt_bgp_mock("eos")
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

    mocker.patch("_states.openconfig_bgp._get_eos_version", return_value=(4, 22))
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer group\n"
        "default neighbor RA02.01:PG-TOR local-as\n"
        "neighbor RA02.01:PG-TOR remote-as 65000\n"
        "default neighbor RA02.01:PG-TOR description\n"
        "default neighbor RA02.01:PG-TOR route-map in\n"
        "default neighbor RA02.01:PG-TOR route-map out\n"
        "default neighbor RA02.01:PG-TOR maximum-routes\n"
        "neighbor RA02.01:PG-TOR send-community"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
        "IPV6_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
    }


@salt_bgp_mock("eos")
def test__generate_peer_group_part__simple(mocker):
    """Test peer-group with simple configuration: no SAFI."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {"local-as": 60000, "peer-as": 65000, "description": "L3_RA"},
        "apply-policy": {
            "config": {"import-policy": ["RM-LAN-IN"], "export-policy": ["RM-LAN-OUT"]}
        },
        "afi-safis": {},
    }

    mocker.patch("_states.openconfig_bgp._get_eos_version", return_value=(4, 22))
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer group\n"
        "neighbor RA02.01:PG-TOR local-as 60000\n"
        "neighbor RA02.01:PG-TOR remote-as 65000\n"
        "neighbor RA02.01:PG-TOR description L3_RA\n"
        "neighbor RA02.01:PG-TOR route-map RM-LAN-IN in\n"
        "neighbor RA02.01:PG-TOR route-map RM-LAN-OUT out\n"
        "default neighbor RA02.01:PG-TOR maximum-routes\n"
        "neighbor RA02.01:PG-TOR send-community"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
        "IPV6_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
    }


@salt_bgp_mock("eos")
def test__generate_peer_group_part_with_safi(mocker):
    """Test peer-group with safi."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {"local-as": 60000, "peer-as": 60001, "description": "L3_RA"},
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

    mocker.patch("_states.openconfig_bgp._get_eos_version", return_value=(4, 22))
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer group\n"
        "neighbor RA02.01:PG-TOR local-as 60000\n"
        "neighbor RA02.01:PG-TOR remote-as 60001\n"
        "neighbor RA02.01:PG-TOR description L3_RA\n"
        "neighbor RA02.01:PG-TOR route-map RM-LAN-IN in\n"
        "neighbor RA02.01:PG-TOR route-map RM-LAN-OUT out\n"
        "neighbor RA02.01:PG-TOR maximum-routes 10000\n"
        "neighbor RA02.01:PG-TOR send-community"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
        "IPV6_UNICAST": (
            "default neighbor RA02.01:PG-TOR route-map in\n"
            "default neighbor RA02.01:PG-TOR route-map out"
        ),
    }
