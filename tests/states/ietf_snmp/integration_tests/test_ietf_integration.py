"""integration test of ietf_snmp for eos."""

import functools
import json
import pytest

import _states.ietf_snmp as STATE_MOD
from _utils import frr_detect_diff, jinja_filters
from jinja2 import BaseLoader, Environment

##
# Tests setup
##


def _get_data_and_expected_result(os_name):
    test_path = "tests/states/ietf_snmp/data/integration_tests/full_config"
    with open(
        f"{test_path}/ietf.json",
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


def _apply_common_mock():
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
    def wrapper(mocker, *args, **kwargs):
        # some mocking
        _apply_common_mock()
        try:
            return func(mocker, *args, **kwargs)
        finally:
            # some cleaning
            del STATE_MOD.__salt__

    return wrapper


##
# Tests
##


@pytest.mark.parametrize("os", ["eos", "junos", "sonic"])
@_mock_then_clean
def test_apply__generate_routing_policy_config__full_config(mocker, os):  # pylint: disable=W0613
    """Test the entire config generation with full and valid config for eos."""

    mocker.patch("_states.ietf_snmp._get_os", return_value=os)
    fake_data, expected_result = _get_data_and_expected_result(os)
    assert STATE_MOD._generate_snmp_config(fake_data, None, saltenv="base") == expected_result
