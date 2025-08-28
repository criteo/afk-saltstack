"""Unit test openconfig_bgp peer-group."""

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("sonic")
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

    peer_groups = {
        "PG-DEFAULT": {
            "peer-group-name": "PG-DEFAULT",
            "config": {"local-as": None, "peer-as": 65001, "description": ""},
            "apply-policy": None,
        }
    }

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(
        config, 65000, {}, peer_groups, None
    )
    assert neighbor_config == (
        "neighbor 192.0.2.1 peer-group PG-DEFAULT\n"
        "no neighbor 192.0.2.1 local-as\n"
        "neighbor 192.0.2.1 description my_neighbor\n"
        "no neighbor 192.0.2.1 password\n"
        "no neighbor 192.0.2.1 timers delayopen\n"
        "no neighbor 192.0.2.1 shutdown"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "no neighbor 192.0.2.1 route-map * in\n"
            "no neighbor 192.0.2.1 route-map * out\n"
            "no neighbor 192.0.2.1 maximum-prefix\n"
            "neighbor 192.0.2.1 activate\n"
            "neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "neighbor 192.0.2.1 send-community"
        ),
        "IPV6_UNICAST": (
            "no neighbor 192.0.2.1 route-map * in\n"
            "no neighbor 192.0.2.1 route-map * out\n"
            "no neighbor 192.0.2.1 maximum-prefix\n"
            "no neighbor 192.0.2.1 activate\n"
            "no neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "no neighbor 192.0.2.1 send-community"
        ),
    }


@salt_bgp_mock("sonic")
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

    peer_groups = {
        "PG-DEFAULT": {
            "peer-group-name": "PG-DEFAULT",
            "config": {"local-as": None, "peer-as": 65001, "description": ""},
            "apply-policy": None,
        }
    }

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(
        config, 65000, {}, peer_groups, None
    )
    assert neighbor_config == (
        "neighbor 192.0.2.1 peer-group PG-DEFAULT\n"
        "neighbor 192.0.2.1 local-as 65002\n"
        "neighbor 192.0.2.1 description my_neighbor\n"
        "no neighbor 192.0.2.1 password\n"
        "no neighbor 192.0.2.1 timers delayopen\n"
        "neighbor 192.0.2.1 shutdown"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "no neighbor 192.0.2.1 route-map * in\n"
            "no neighbor 192.0.2.1 route-map * out\n"
            "no neighbor 192.0.2.1 maximum-prefix\n"
            "neighbor 192.0.2.1 activate\n"
            "neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "neighbor 192.0.2.1 send-community"
        ),
        "IPV6_UNICAST": (
            "no neighbor 192.0.2.1 route-map * in\n"
            "no neighbor 192.0.2.1 route-map * out\n"
            "no neighbor 192.0.2.1 maximum-prefix\n"
            "no neighbor 192.0.2.1 activate\n"
            "no neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "no neighbor 192.0.2.1 send-community"
        ),
    }


@salt_bgp_mock("sonic")
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

    peer_groups = {
        "PG-TOR": {
            "peer-group-name": "PG-TOR",
            "config": {"local-as": None, "peer-as": 65001, "description": ""},
            "apply-policy": None,
        }
    }

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(
        config, 65000, {}, peer_groups, None
    )
    assert neighbor_config == (
        "neighbor 2001:db8::1 peer-group PG-TOR\n"
        "no neighbor 2001:db8::1 local-as\n"
        "neighbor 2001:db8::1 description my_neighbor\n"
        "no neighbor 2001:db8::1 password\n"
        "no neighbor 2001:db8::1 timers delayopen\n"
        "no neighbor 2001:db8::1 shutdown"
    )
    assert safi_config == {
        "IPV4_UNICAST": (
            "no neighbor 2001:db8::1 route-map * in\n"
            "no neighbor 2001:db8::1 route-map * out\n"
            "no neighbor 2001:db8::1 maximum-prefix\n"
            "no neighbor 2001:db8::1 activate\n"
            "no neighbor 2001:db8::1 soft-reconfiguration inbound\n"
            "no neighbor 2001:db8::1 send-community"
        ),
        "IPV6_UNICAST": (
            "no neighbor 2001:db8::1 route-map * in\n"
            "no neighbor 2001:db8::1 route-map * out\n"
            "no neighbor 2001:db8::1 maximum-prefix\n"
            "no neighbor 2001:db8::1 activate\n"
            "no neighbor 2001:db8::1 soft-reconfiguration inbound\n"
            "no neighbor 2001:db8::1 send-community"
        ),
    }


@salt_bgp_mock("sonic")
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

    peer_groups = {
        "PG-DEFAULT": {
            "peer-group-name": "PG-DEFAULT",
            "config": {"local-as": None, "peer-as": 65001, "description": ""},
            "apply-policy": None,
        }
    }

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(
        config, 65000, {}, peer_groups, None
    )
    assert neighbor_config == (
        "neighbor 192.0.2.1 peer-group PG-DEFAULT\n"
        "neighbor 192.0.2.1 local-as 65002\n"
        "neighbor 192.0.2.1 description my_neighbor\n"
        "neighbor 192.0.2.1 password thisisasecret\n"
        "no neighbor 192.0.2.1 timers delayopen\n"
        "no neighbor 192.0.2.1 shutdown"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "neighbor 192.0.2.1 route-map RM-2-IN in\n"
            "neighbor 192.0.2.1 route-map RM-2-OUT out\n"
            "neighbor 192.0.2.1 maximum-prefix 1000\n"
            "neighbor 192.0.2.1 activate\n"
            "neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "neighbor 192.0.2.1 send-community"
        ),
        "IPV6_UNICAST": (
            "neighbor 192.0.2.1 route-map RM-1-IN in\n"
            "neighbor 192.0.2.1 route-map RM-1-OUT out\n"
            "neighbor 192.0.2.1 maximum-prefix 1000\n"
            "neighbor 192.0.2.1 activate\n"
            "neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "neighbor 192.0.2.1 send-community"
        ),
    }


@salt_bgp_mock("sonic")
def test__generate_neighbor_part__delay_open_timer(mocker):
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
        "timers": {"config": {"delay-open-timer": 5}},
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

    peer_groups = {
        "PG-DEFAULT": {
            "peer-group-name": "PG-DEFAULT",
            "config": {"local-as": None, "peer-as": 65001, "description": ""},
            "apply-policy": None,
        }
    }

    neighbor_config, safi_config = STATE_MOD._generate_neighbor_config(
        config, 65000, {}, peer_groups, None
    )
    assert neighbor_config == (
        "neighbor 192.0.2.1 peer-group PG-DEFAULT\n"
        "neighbor 192.0.2.1 local-as 65002\n"
        "neighbor 192.0.2.1 description my_neighbor\n"
        "neighbor 192.0.2.1 password thisisasecret\n"
        "neighbor 192.0.2.1 timers delayopen 5\n"
        "no neighbor 192.0.2.1 shutdown"
    )

    assert safi_config == {
        "IPV4_UNICAST": (
            "neighbor 192.0.2.1 route-map RM-2-IN in\n"
            "neighbor 192.0.2.1 route-map RM-2-OUT out\n"
            "neighbor 192.0.2.1 maximum-prefix 1000\n"
            "neighbor 192.0.2.1 activate\n"
            "neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "neighbor 192.0.2.1 send-community"
        ),
        "IPV6_UNICAST": (
            "neighbor 192.0.2.1 route-map RM-1-IN in\n"
            "neighbor 192.0.2.1 route-map RM-1-OUT out\n"
            "neighbor 192.0.2.1 maximum-prefix 1000\n"
            "neighbor 192.0.2.1 activate\n"
            "neighbor 192.0.2.1 soft-reconfiguration inbound\n"
            "neighbor 192.0.2.1 send-community"
        ),
    }
