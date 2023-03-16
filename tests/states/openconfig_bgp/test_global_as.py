import pytest
import _states.openconfig_bgp as STATE_MOD

from salt.exceptions import CommandExecutionError


def test__get_global_as__bootstrap(mocker):
    """Test bootstrap scenario.

    Expected ASN = 65000 && current ASN = None.
    """
    asn = mocker.Mock()
    global_config = {"global": {"config": {"as": 65000}}}

    STATE_MOD.__salt__ = {"criteo_bgp.get_global_as": asn}

    asn.return_value = None
    assert STATE_MOD._get_global_as(global_config, "sonic") == 65000

    del STATE_MOD.__salt__


def test__get_global_as__only_in_cmdb(mocker):
    """Test global conf only in CMDB.

    Expected ASN = None && current ASN = 65000.
    """
    asn = mocker.Mock()
    asn.return_value = 65000
    STATE_MOD.__salt__ = {"criteo_bgp.get_global_as": asn}

    assert STATE_MOD._get_global_as({}, "sonic") == 65000

    del STATE_MOD.__salt__


def test__get_global_as__both_cmdb_and_current(mocker):
    """Test normal scenario.

    Expected ASN = 65001 && current ASN = 65001.
    """
    asn = mocker.Mock()
    asn.return_value = 65001
    STATE_MOD.__salt__ = {"criteo_bgp.get_global_as": asn}

    global_config = {"global": {"config": {"as": 65001}}}

    assert STATE_MOD._get_global_as(global_config, "sonic") == 65001

    del STATE_MOD.__salt__


def test___get_global_as(mocker):
    """Test mistmatch scenario.

    Expected ASN = 65002 && current ASN = 65003.
    """
    asn = mocker.Mock()
    asn.return_value = 65003
    STATE_MOD.__salt__ = {"criteo_bgp.get_global_as": asn}

    global_config = {"global": {"config": {"as": 65002}}}

    with pytest.raises(CommandExecutionError):
        STATE_MOD._get_global_as(global_config, "sonic")

    del STATE_MOD.__salt__
