"""integration test of openconfig_routing_policy for JunOS."""
import functools
import json

import _states.openconfig_routing_policy as STATE_MOD
import _utils.jinja_filters as STATE_UTIL
import pytest
from jinja2 import BaseLoader, Environment

##
# Tests setup
##


def _get_data_and_expected_result(os_name):
    test_path = "tests/states/openconfig_routing_policy/data/integration_tests"
    with open(
        f"{test_path}/openconfig.json",
        encoding="utf-8",
    ) as fd:
        fake_data = json.load(fd)

    with open(
        f"{test_path}/expected_result_{os_name}.txt",
        encoding="utf-8",
    ) as fd:
        expected_result = fd.read()

    return fake_data, expected_result


def _mock_apply_template_on_contents(contents, template, context, *_, **__):
    assert template == "jinja"
    loader = Environment(loader=BaseLoader)
    template = loader.from_string(contents)
    return template.render(**context)


def _mock_get_file_str(template_name, *_, **__):
    # removing salt:// prefix in path file
    template_name = template_name[7:]
    with open(template_name, encoding="utf-8") as fd:
        content = fd.read()
        return content


def _apply_common_mock(mocker):
    mocker.patch("_states.openconfig_routing_policy._get_os", return_value="junos")
    STATE_MOD.__salt__ = {
        "file.apply_template_on_contents": _mock_apply_template_on_contents,
        "cp.get_file_str": _mock_get_file_str,
    }
    STATE_MOD.__utils__ = {
        "jinja_filters.format_route_policy_name": STATE_UTIL.format_route_policy_name,
        "jinja_filters.deep_get": STATE_UTIL.deep_get,
    }


def _mock_then_clean(func):
    @functools.wraps(func)
    def wrapper(mocker):
        # some mocking
        _apply_common_mock(mocker)
        try:
            return func(mocker)
        finally:
            # some cleaning
            del STATE_MOD.__salt__

    return wrapper


##
# Tests
##


@_mock_then_clean
def test_apply__generate_routing_policy_config__full_config_junos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for JunOS."""
    fake_data, expected_result = _get_data_and_expected_result("junos")
    assert (
        STATE_MOD._generate_routing_policy_config(
            fake_data["routing-policy"], fake_data["bgp"], None, saltenv="base"
        )
        == expected_result
    )


@_mock_then_clean
def test__juniper_bgp_one_safi_policy(mocker):
    """Test Juniper when only a SAFI has a policy in import only."""
    bgp_config = {
        "bgp": {
            "neighbors": {
                "neighbor": [
                    {
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
                        "afi-safis": {
                            "afi-safi": [
                                {
                                    "afi-safi-name": "IPV4_UNICAST",
                                    "config": {"afi-safi-name": "IPV4_UNICAST", "enabled": True},
                                    "apply-policy": {"config": {"import-policy": ["RM-TEST"]}},
                                    "ipv4-unicast": {
                                        "prefix-limit": {"config": {"max-prefixes": 0}}
                                    },
                                }
                            ]
                        },
                    },
                ],
            },
        },
    }

    fake_data, _ = _get_data_and_expected_result("junos")

    out = STATE_MOD._generate_routing_policy_config(
        fake_data["routing-policy"], bgp_config["bgp"], None, saltenv="base"
    )
    assert out == (
        "delete policy-options community CL-LOCAL\n"
        "set policy-options community CL-LOCAL members 65000:100.\n"
        "delete policy-options community CL-MAIN\n"
        "set policy-options community CL-MAIN members 649..:20000\n"
        "delete policy-options community CL-SERVICE\n"
        "set policy-options community CL-SERVICE members 65000:5....\n"
        "delete policy-options community CL-DEFAULT\n"
        "set policy-options community CL-DEFAULT members 65000:60000\n"
        "delete policy-options community CL-LOCATION\n"
        "set policy-options community CL-LOCATION members 65000:65001\n"
        "delete policy-options community CL-CLOS_INFRA\n"
        "set policy-options community CL-CLOS_INFRA members 65000:10100\n"
        "delete policy-options community CL-SERVER\n"
        "set policy-options community CL-SERVER members 65000:10200\n"
        "delete policy-options route-filter-list PF-LOOPBACK_IPV4\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV4 10.0.0.0/22 exact\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV4 10.0.1.0/22 exact\n"
        "delete policy-options route-filter-list PF-LOOPBACK_IPV6\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV6 2001:db8:1::/64 exact\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV6 2001:db8:1::/128 exact\n"
        "delete policy-options policy-statement RM-TEST\n"
        "delete policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST\n"
        "set policy-options policy-statement RM-TEST term 10 from route-filter-list PF-LOOPBACK_IPV4\n"
        "set policy-options policy-statement RM-TEST term 10 from protocol direct\n"
        "set policy-options policy-statement RM-TEST term 10 from local-preference 1234\n"
        "set policy-options policy-statement RM-TEST term 10 from community CL-LOCAL\n"
        "set policy-options policy-statement RM-TEST term 10 then origin egp\n"
        "set policy-options policy-statement RM-TEST term 10 then local-preference 5678\n"
        "set policy-options policy-statement RM-TEST term 10 then metric 250\n"
        "set policy-options policy-statement RM-TEST term 10 then as-path-prepend 65000 65000 65000\n"
        "delete policy-options community AUTOGENERATED::RM-TEST:10\n"
        "set policy-options community AUTOGENERATED::RM-TEST:10 members 65000:50000\n"
        "set policy-options policy-statement RM-TEST term 10 then community set AUTOGENERATED::RM-TEST:10\n"
        "set policy-options policy-statement RM-TEST term 10 then reject\n"
        "set policy-options policy-statement RM-TEST then reject\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 from family inet\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 from route-filter-list PF-LOOPBACK_IPV4\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 from protocol direct\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 from local-preference 1234\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 from community CL-LOCAL\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 then origin egp\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 then local-preference 5678\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 then metric 250\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 then as-path-prepend 65000 65000 65000\n"
        "delete policy-options community AUTOGENERATED::RM-TEST:10\n"
        "set policy-options community AUTOGENERATED::RM-TEST:10 members 65000:50000\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 then community set AUTOGENERATED::RM-TEST:10\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST term 10 then reject\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV4_UNICAST then reject\n"
        "delete policy-options policy-statement RM-TEST-OUT\n"
        "set policy-options policy-statement RM-TEST-OUT term 10 then reject\n"
        "set policy-options policy-statement RM-TEST-OUT then reject"
    )

@_mock_then_clean
def test__juniper_bgp_one_safi_policy_ipv6(mocker):
    """Test Juniper when only a SAFI has a policy in import only."""
    bgp_config = {
        "bgp": {
            "neighbors": {
                "neighbor": [
                    {
                        "neighbor-address": "2001:db8::.1",
                        "config": {
                            "peer-group": "PG-DEFAULT",
                            "neighbor-address": "2001:db8::.1",
                            "enabled": True,
                            "peer-as": 65001,
                            "local-as": 65000,
                            "auth-password": "",
                            "description": "my_neighbor",
                            "peer-type": None,
                            "remove-private-as": None,
                            "send-community": "NONE",
                        },
                        "afi-safis": {
                            "afi-safi": [
                                {
                                    "afi-safi-name": "IPV6_UNICAST",
                                    "config": {"afi-safi-name": "IPV6_UNICAST", "enabled": True},
                                    "apply-policy": {"config": {"import-policy": ["RM-TEST"]}},
                                    "ipv4-unicast": {
                                        "prefix-limit": {"config": {"max-prefixes": 0}}
                                    },
                                }
                            ]
                        },
                    },
                ],
            },
        },
    }

    fake_data, _ = _get_data_and_expected_result("junos")

    out = STATE_MOD._generate_routing_policy_config(
        fake_data["routing-policy"], bgp_config["bgp"], None, saltenv="base"
    )
    assert out == (
        "delete policy-options community CL-LOCAL\n"
        "set policy-options community CL-LOCAL members 65000:100.\n"
        "delete policy-options community CL-MAIN\n"
        "set policy-options community CL-MAIN members 649..:20000\n"
        "delete policy-options community CL-SERVICE\n"
        "set policy-options community CL-SERVICE members 65000:5....\n"
        "delete policy-options community CL-DEFAULT\n"
        "set policy-options community CL-DEFAULT members 65000:60000\n"
        "delete policy-options community CL-LOCATION\n"
        "set policy-options community CL-LOCATION members 65000:65001\n"
        "delete policy-options community CL-CLOS_INFRA\n"
        "set policy-options community CL-CLOS_INFRA members 65000:10100\n"
        "delete policy-options community CL-SERVER\n"
        "set policy-options community CL-SERVER members 65000:10200\n"
        "delete policy-options route-filter-list PF-LOOPBACK_IPV4\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV4 10.0.0.0/22 exact\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV4 10.0.1.0/22 exact\n"
        "delete policy-options route-filter-list PF-LOOPBACK_IPV6\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV6 2001:db8:1::/64 exact\n"
        "set policy-options route-filter-list PF-LOOPBACK_IPV6 2001:db8:1::/128 exact\n"
        "delete policy-options policy-statement RM-TEST\n"
        "delete policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST\n"
        "set policy-options policy-statement RM-TEST term 10 from route-filter-list PF-LOOPBACK_IPV4\n"
        "set policy-options policy-statement RM-TEST term 10 from protocol direct\n"
        "set policy-options policy-statement RM-TEST term 10 from local-preference 1234\n"
        "set policy-options policy-statement RM-TEST term 10 from community CL-LOCAL\n"
        "set policy-options policy-statement RM-TEST term 10 then origin egp\n"
        "set policy-options policy-statement RM-TEST term 10 then local-preference 5678\n"
        "set policy-options policy-statement RM-TEST term 10 then metric 250\n"
        "set policy-options policy-statement RM-TEST term 10 then as-path-prepend 65000 65000 65000\n"
        "delete policy-options community AUTOGENERATED::RM-TEST:10\n"
        "set policy-options community AUTOGENERATED::RM-TEST:10 members 65000:50000\n"
        "set policy-options policy-statement RM-TEST term 10 then community set AUTOGENERATED::RM-TEST:10\n"
        "set policy-options policy-statement RM-TEST term 10 then reject\n"
        "set policy-options policy-statement RM-TEST then reject\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 from family inet6\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 from route-filter-list PF-LOOPBACK_IPV4\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 from protocol direct\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 from local-preference 1234\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 from community CL-LOCAL\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 then origin egp\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 then local-preference 5678\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 then metric 250\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 then as-path-prepend 65000 65000 65000\n"
        "delete policy-options community AUTOGENERATED::RM-TEST:10\n"
        "set policy-options community AUTOGENERATED::RM-TEST:10 members 65000:50000\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 then community set AUTOGENERATED::RM-TEST:10\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST term 10 then reject\n"
        "set policy-options policy-statement AUTOGENERATED::RM-TEST::IPV6_UNICAST then reject\n"
        "delete policy-options policy-statement RM-TEST-OUT\n"
        "set policy-options policy-statement RM-TEST-OUT term 10 then reject\n"
        "set policy-options policy-statement RM-TEST-OUT then reject"
    )
