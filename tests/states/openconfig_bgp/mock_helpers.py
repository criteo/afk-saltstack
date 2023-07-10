import functools

import _states.openconfig_bgp as STATE_MOD
import _utils.jinja_filters as STATE_UTIL
from tests.common import mock_apply_template_on_contents, mock_get_file_str
from tests.states.openconfig_bgp.integration_tests.common_bgp_integration import mock_get_neighbors


def _mock_pillar_eos(*args, **__):
    if args and args[0] == "vrf":
        return {"default": ""}

    return {}


def _mock_pillar_junos(*args, **__):
    if args and args[0] == "vrf":
        return {"default": "prod"}

    return {}


def _mock_pillar_sonic(*args, **__):
    if args and args[0] == "vrf":
        return {"no": ""}

    return {}


_PILLAR_MOCKER = {
    "eos": _mock_pillar_eos,
    "junos": _mock_pillar_junos,
    "sonic": _mock_pillar_sonic,
}


def _apply_common_mock(mocker, network_os):
    mocker.patch("_states.openconfig_bgp._get_os", return_value=network_os)

    asn = mocker.Mock()
    asn.return_value = 65000

    STATE_MOD.__salt__ = {
        "criteo_bgp.get_global_as": asn,
        "file.apply_template_on_contents": mock_apply_template_on_contents,
        "cp.get_file_str": mock_get_file_str,
        "pillar.get": _PILLAR_MOCKER[network_os],
        "criteo_bgp.get_neighbors": mock_get_neighbors,
    }
    STATE_MOD.__utils__ = {
        "jinja_filters.format_route_policy_name": STATE_UTIL.format_route_policy_name
    }


def salt_bgp_mock(network_os):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(mocker):
            # some mocking
            _apply_common_mock(mocker, network_os)
            try:
                return func(mocker)
            finally:
                # some cleaning
                del STATE_MOD.__salt__
                del STATE_MOD.__utils__

        return wrapper

    return decorator
