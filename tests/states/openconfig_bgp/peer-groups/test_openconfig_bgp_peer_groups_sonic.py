"""Unit test openconfig_bgp peer-group."""
import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("sonic")
def test__generate_peer_group_part__without_remote_as(mocker):
    """Test peer-group with no remote-as.

    Note: It should never happen as an opiniated choice was made to make
    remote-as mandatory (to avoid complexity on FRR).
    """
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {
            "local-as": None,
            "description": "",
        },
        "apply-policy": {},
        "afis-safis": {},
    }
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)

    # we ensure the remote-as is never removed (no "no command")
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer-group\n"
        "no neighbor RA02.01:PG-TOR local-as\n"
        "no neighbor RA02.01:PG-TOR description"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "no neighbor RA02.01:PG-TOR route-map * in\n"
            "no neighbor RA02.01:PG-TOR route-map * out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"
        ),
        "IPV6_UNICAST": (
            "no neighbor RA02.01:PG-TOR route-map * in\n"
            "no neighbor RA02.01:PG-TOR route-map * out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"
        ),
    }


@salt_bgp_mock("sonic")
def test__generate_peer_group_part__minimal(mocker):
    """Test peer-group with no specific configuration."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {
            "local-as": None,
            "peer-as": "65000",
            "description": "",
        },
        "apply-policy": {},
        "afis-safis": {},
    }
    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer-group\n"
        "no neighbor RA02.01:PG-TOR local-as\n"
        "neighbor RA02.01:PG-TOR remote-as 65000\n"
        "no neighbor RA02.01:PG-TOR description"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "no neighbor RA02.01:PG-TOR route-map * in\n"
            "no neighbor RA02.01:PG-TOR route-map * out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"

        ),
        "IPV6_UNICAST": (
            "no neighbor RA02.01:PG-TOR route-map * in\n"
            "no neighbor RA02.01:PG-TOR route-map * out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"

        ),
    }


@salt_bgp_mock("sonic")
def test__generate_peer_group_part__simple(mocker):
    """Test peer-group with simple configuration: no SAFI."""
    config = {
        "peer-group-name": "RA02.01:PG-TOR",
        "config": {"local-as": 60000, "peer-as": 65000, "description": "L3_RA"},
        "apply-policy": {
            "config": {"import-policy": ["RM-LAN-IN"], "export-policy": ["RM-LAN-OUT"]}
        },
        "afis-safis": {},
    }

    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer-group\n"
        "neighbor RA02.01:PG-TOR local-as 60000\n"
        "neighbor RA02.01:PG-TOR remote-as 65000\n"
        "neighbor RA02.01:PG-TOR description L3_RA"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "neighbor RA02.01:PG-TOR route-map RM-LAN-IN in\n"
            "neighbor RA02.01:PG-TOR route-map RM-LAN-OUT out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"
        ),
        "IPV6_UNICAST": (
            "neighbor RA02.01:PG-TOR route-map RM-LAN-IN in\n"
            "neighbor RA02.01:PG-TOR route-map RM-LAN-OUT out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"
        ),
    }


@salt_bgp_mock("sonic")
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

    pg_config, safi_config = STATE_MOD._generate_peer_group(config, {}, None)
    assert pg_config == (
        "neighbor RA02.01:PG-TOR peer-group\n"
        "neighbor RA02.01:PG-TOR local-as 60000\n"
        "neighbor RA02.01:PG-TOR remote-as 60001\n"
        "neighbor RA02.01:PG-TOR description L3_RA"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "neighbor RA02.01:PG-TOR route-map RM-LAN-IN in\n"
            "neighbor RA02.01:PG-TOR route-map RM-LAN-OUT out\n"
            "neighbor RA02.01:PG-TOR maximum-prefix 10000\n"
            "neighbor RA02.01:PG-TOR send-community"
        ),
        "IPV6_UNICAST": (
            "neighbor RA02.01:PG-TOR route-map RM-LAN-IN in\n"
            "neighbor RA02.01:PG-TOR route-map RM-LAN-OUT out\n"
            "no neighbor RA02.01:PG-TOR maximum-prefix\n"
            "neighbor RA02.01:PG-TOR send-community"
        ),
    }
