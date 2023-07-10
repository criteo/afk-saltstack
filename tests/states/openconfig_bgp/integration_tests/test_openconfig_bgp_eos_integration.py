"""integration test of openconfig_bgp for EOS."""
import pytest

import _states.openconfig_bgp as STATE_MOD
from tests.states.openconfig_bgp.integration_tests.common_bgp_integration import (
    assert_expected_integration_result,
)
from tests.states.openconfig_bgp.mock_helpers import salt_bgp_mock


@salt_bgp_mock("eos")
def test_apply__generate_bgp_config__empty_config_eos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with empty data for eos."""
    with pytest.raises(KeyError):
        assert STATE_MOD._generate_bgp_config({}, remove_extras=False, rules=None, saltenv="base")


@salt_bgp_mock("eos")
def test_apply__generate_bgp_config__full_config_eos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for eos."""
    fake_data, expected_result = assert_expected_integration_result("full_config", "eos")
    mocker.patch("_states.openconfig_bgp._get_eos_version", return_value=(4, 22))
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("eos")
def test_apply__generate_bgp_config__v4_only_eos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for eos."""
    fake_data, expected_result = assert_expected_integration_result("v4_only", "eos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("eos")
def test_apply__generate_bgp_config__v6_only_eos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for eos."""
    fake_data, expected_result = assert_expected_integration_result("v6_only", "eos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=False, rules=None, saltenv="base"
        )
        == expected_result
    )


@salt_bgp_mock("eos")
def test__apply__generate_bgp_config__with_extras_eos(mocker):  # pylint: disable=W0613
    """Test the config generation with peers to remove."""
    fake_data, expected_result = assert_expected_integration_result("with_extras", "eos")
    assert (
        STATE_MOD._generate_bgp_config(
            fake_data["bgp"], remove_extras=True, rules=None, saltenv="base"
        )
        == expected_result
    )
