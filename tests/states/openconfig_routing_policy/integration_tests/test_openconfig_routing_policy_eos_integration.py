"""integration test of openconfig_routing_policy for eos."""
import functools
import json

import _states.openconfig_routing_policy as STATE_MOD
from _utils import frr_detect_diff, jinja_filters
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
    mocker.patch("_states.openconfig_routing_policy._get_os", return_value="eos")
    STATE_MOD.__salt__ = {
        "file.apply_template_on_contents": _mock_apply_template_on_contents,
        "cp.get_file_str": _mock_get_file_str,
        "eos.get_bgp_config": lambda *_: (""),
    }
    STATE_MOD.__utils__ = {
        "frr_detect_diff.get_objects": frr_detect_diff.get_objects,
        "jinja_filters.format_route_policy_name": jinja_filters.format_route_policy_name,
        "jinja_filters.deep_get": jinja_filters.deep_get,
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
def test_apply__generate_routing_policy_config__full_config_eos(mocker):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for eos."""
    mocker.patch("_states.openconfig_routing_policy._get_eos_version", return_value=(4, 22))
    fake_data, expected_result = _get_data_and_expected_result("eos")
    assert (
        STATE_MOD._generate_routing_policy_config(
            fake_data["routing-policy"], fake_data["bgp"], None, saltenv="base"
        )
        == expected_result
    )


@_mock_then_clean
def test_apply__generate_routing_policy_config__full_config_eos_before_4_22(
    mocker,
):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for eos."""
    mocker.patch("_states.openconfig_routing_policy._get_eos_version", return_value=(4, 17))
    fake_data, expected_result = _get_data_and_expected_result("eos_before_4_22")
    assert (
        STATE_MOD._generate_routing_policy_config(
            fake_data["routing-policy"], fake_data["bgp"], None, saltenv="base"
        )
        == expected_result
    )
