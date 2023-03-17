"""Functional test of openconfig_bgp for SONiC."""
import pytest

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.functional_tests.common_bgp_functional import (
    assert_expected_functional_result,
)
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("sonic")
def test_apply__generate_bgp_config__empty_config_sonic(mocker):  # pylint: disable=W0613
    """Test the entire config generation with empty data for SONiC."""
    with pytest.raises(KeyError):
        assert STATE_MOD._generate_bgp_config({}, remove_extras=False, rules=None, saltenv="base")


@salt_bgp_mock("sonic")
def test_apply__generate_bgp_config__full_config_sonic(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for SONiC."""
    fake_data, expected_result = assert_expected_functional_result("full_config", "sonic")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("sonic")
def test_apply__generate_bgp_config__v4_only_sonic(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for SONiC."""
    fake_data, expected_result = assert_expected_functional_result("v4_only", "sonic")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("sonic")
def test_apply__generate_bgp_config__v6_only_sonic(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for SONiC."""
    fake_data, expected_result = assert_expected_functional_result("v6_only", "sonic")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("sonic")
def test__apply__generate_bgp_config__with_extras_sonic(mocker):  # pylint: disable=W0613
    """Test the config generation with peers to remove."""
    fake_data, expected_result = assert_expected_functional_result("with_extras", "sonic")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=True, rules=None, saltenv="base"
        )
        == expected_result
    )
