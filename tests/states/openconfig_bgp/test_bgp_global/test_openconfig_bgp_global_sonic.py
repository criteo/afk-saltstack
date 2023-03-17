"""Unit test openconfig_bgp global configuration."""

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("sonic")
def test__generate_global_configuration_minimal(mocker):
    config = {
        "config": {"as": 65000},
    }
    assert STATE_MOD._generate_global_conf_part(config, None) == (
        "bgp log-neighbor-changes\n"
        "bgp bestpath as-path multipath-relax\n"
        "no bgp router-id\n"
        "distance bgp 20 200 200\n"
        "no bgp graceful-restart\n"
        "no bgp graceful-restart preserve-fw-state\n"
        "no bgp graceful-restart restart-time\n"
        "address-family ipv4 unicast\n"
        "  no maximum-paths\n"
        "  no maximum-paths ibgp\n"
        "!\n"
        "address-family ipv6 unicast\n"
        "  no maximum-paths\n"
        "  no maximum-paths ibgp"
    )


@salt_bgp_mock("sonic")
def test__generate_global_configuration_minimal2(mocker):
    config = {
        "config": {"as": 65000},
        "default-route-distance": {"config": {"external-route-distance": 20}},
        "graceful-restart": {
            "config": {"enabled": True},
        },
    }
    assert STATE_MOD._generate_global_conf_part(config, None) == (
        "bgp log-neighbor-changes\n"
        "bgp bestpath as-path multipath-relax\n"
        "no bgp router-id\n"
        "distance bgp 20 200 200\n"
        "bgp graceful-restart\n"
        "bgp graceful-restart preserve-fw-state\n"
        "no bgp graceful-restart restart-time\n"
        "address-family ipv4 unicast\n"
        "  no maximum-paths\n"
        "  no maximum-paths ibgp\n"
        "!\n"
        "address-family ipv6 unicast\n"
        "  no maximum-paths\n"
        "  no maximum-paths ibgp"
    )


@salt_bgp_mock("sonic")
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
        "bgp log-neighbor-changes\n"
        "bgp bestpath as-path multipath-relax\n"
        "bgp router-id 127.0.0.1\n"
        "distance bgp 20 170 170\n"
        "bgp graceful-restart\n"
        "bgp graceful-restart preserve-fw-state\n"
        "bgp graceful-restart restart-time 240\n"
        "address-family ipv4 unicast\n"
        "  maximum-paths 128\n"
        "  maximum-paths ibgp 128\n"
        "!\n"
        "address-family ipv6 unicast\n"
        "  maximum-paths 128\n"
        "  maximum-paths ibgp 128"
    )
