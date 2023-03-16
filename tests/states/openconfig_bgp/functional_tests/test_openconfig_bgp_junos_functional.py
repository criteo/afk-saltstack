"""Functional test of openconfig_bgp for JunOS."""
import pytest

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.functional_tests.common_bgp_functional import (
    assert_expected_functional_result,
)
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("junos")
def test_apply__generate_bgp_config__empty_config_junos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with empty data for JunOS."""
    with pytest.raises(KeyError):
        assert STATE_MOD._generate_bgp_config({}, remove_extras=False, rules=None, saltenv="base")


@salt_bgp_mock("junos")
def test_apply__generate_bgp_config__full_config_junos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for JunOS."""
    fake_data, expected_result = assert_expected_functional_result("full_config", "junos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("junos")
def test_apply__generate_bgp_config__v4_only_junos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for JunOS."""
    fake_data, expected_result = assert_expected_functional_result("v4_only", "junos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("junos")
def test_apply__generate_bgp_config__v6_only_junos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for JunOS."""
    fake_data, expected_result = assert_expected_functional_result("v6_only", "junos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("junos")
def test__apply__generate_bgp_config__with_extras_junos(mocker):  # pylint: disable=W0613
    """Test the config generation with peers to remove."""
    fake_data, expected_result = assert_expected_functional_result("with_extras", "junos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=True, rules=None, saltenv="base"
        )
        == expected_result
    )
