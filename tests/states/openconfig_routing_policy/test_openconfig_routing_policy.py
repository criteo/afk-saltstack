"""Unit tests of openconfig_routing_policy."""
import pytest
import _states.openconfig_routing_policy as STATE_MOD


def test__convert_range_cisco_like__ipv4():
    """Test convert_range_eos ipv4."""
    assert STATE_MOD._convert_range_cisco_like("exact", "192.0.2.0/24") == ""
    assert STATE_MOD._convert_range_cisco_like("24..28", "192.0.2.0/24") == "le 28"
    assert STATE_MOD._convert_range_cisco_like("32..32", "192.0.2.0/24") == "ge 32"
    assert STATE_MOD._convert_range_cisco_like("25..28", "192.0.2.0/24") == "ge 25 le 28"
    assert STATE_MOD._convert_range_cisco_like("25..32", "192.0.2.0/24") == "ge 25 le 32"

    with pytest.raises(ValueError):
        assert STATE_MOD._convert_range_cisco_like("-1..28", "192.0.2.0/24")
        assert STATE_MOD._convert_range_cisco_like("0..28", "192.0.2.0/24")
        assert STATE_MOD._convert_range_cisco_like("25..0", "192.0.2.0/24")
        assert STATE_MOD._convert_range_cisco_like("25..64", "192.0.2.0/24")


def test__convert_range_cisco_like__ipv6():
    """Test convert_range_eos ipv6."""
    assert STATE_MOD._convert_range_cisco_like("exact", "2001:DB8::/32", ipv6=True) == ""
    assert STATE_MOD._convert_range_cisco_like("32..34", "2001:DB8::/32", ipv6=True) == "le 34"
    assert STATE_MOD._convert_range_cisco_like("128..128", "2001:DB8::/32", ipv6=True) == "ge 128"
    assert (
        STATE_MOD._convert_range_cisco_like("33..34", "2001:DB8::/32", ipv6=True) == "ge 33 le 34"
    )
    assert (
        STATE_MOD._convert_range_cisco_like("33..128", "2001:DB8::/32", ipv6=True) == "ge 33 le 128"
    )

    with pytest.raises(ValueError):
        assert STATE_MOD._convert_range_cisco_like("-1..33", "2001:DB8::/32", ipv6=True)
        assert STATE_MOD._convert_range_cisco_like("0..33", "2001:DB8::/32", ipv6=True)
        assert STATE_MOD._convert_range_cisco_like("33..0", "2001:DB8::/32", ipv6=True)
        assert STATE_MOD._convert_range_cisco_like("33..64", "2001:DB8::/32", ipv6=True)
