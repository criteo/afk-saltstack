"""Unit test for bgp removal safeguards in openconfig_bgp."""

import _states.openconfig_bgp as STATE_MOD

RULES = [
    {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 2,
        "remove_down_only": True,
    },
    {
        "field": "description",
        "contains": "server",
        "minimum_up": 1,
        "remove_down_only": False,
    },
]

##
# Test _is_rule_respected()
##


def test__is_rule_respected__not_concerned():
    """test is_rule_respected when neighbor not matching the rule."""
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 2,
        "remove_down_only": False,
    }

    neighbor = {
        "state": "up",
        "peer_group": "PG-SPINE",
        "remote_address": "192.0.2.1",
    }

    assert STATE_MOD._is_rule_respected(rule, neighbor, {}, []) is True


def test__is_rule_respected__down_remove_down_only():
    """test is_rule_respected when removing down session only and session is down."""
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 0,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "down",
        "peer_group": "PG-TOR",
        "remote_address": "192.0.2.1",
    }

    assert STATE_MOD._is_rule_respected(rule, neighbor, {}, []) is True


def test__is_rule_respected__up_remove_down_only():
    """test is_rule_respected when removing down session only and session is up."""
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 0,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "up",
        "peer_group": "PG-TOR",
        "remote_address": "192.0.2.1",
    }

    assert STATE_MOD._is_rule_respected(rule, neighbor, {}, []) is False


def test__is_rule_respected__peer_group__below_minimum():
    """Test is_rule_respected with peer_group filter, below minimum."""
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 2,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "down",
        "peer_group": "PG-TOR",
        "remote_address": "192.0.2.1",
    }

    all_neighbors = [
        neighbor,
        {
            "state": "up",
            "peer_group": "PG-TOR",
            "remote_address": "192.0.2.5",
        },
        {
            "state": "up",
            "peer_group": "PG-SPINE",
            "remote_address": "192.0.2.7",
        },
    ]

    assert STATE_MOD._is_rule_respected(rule, neighbor, all_neighbors, []) is False


def test__is_rule_respected__peer_group__below_minimum_one_already_removed():
    """Test is_rule_respected with peer_group filter, below minimum.

    Because one already being removed.
    """
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 1,
        "remove_down_only": False,
    }

    neighbor = {
        "state": "up",
        "peer_group": "PG-TOR",
        "remote_address": "192.0.2.1",
    }

    all_neighbors = [
        neighbor,
        {
            "state": "up",
            "peer_group": "PG-TOR",
            "remote_address": "192.0.2.5",
        },
        {
            "state": "up",
            "peer_group": "PG-SPINE",
            "remote_address": "192.0.2.7",
        },
    ]

    to_remove = [
        {
            "state": "up",
            "peer_group": "PG-TOR",
            "remote_address": "192.0.2.5",
        },
    ]

    assert STATE_MOD._is_rule_respected(rule, neighbor, all_neighbors, to_remove) is False


def test__is_rule_respected__peer_group__equal_to_minimum():
    """Test is_rule_respected with peer_group filter, equal to minimum."""
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 1,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "down",
        "peer_group": "PG-TOR",
        "remote_address": "192.0.2.1",
    }

    all_neighbors = [
        neighbor,
        {
            "state": "up",
            "peer_group": "PG-TOR",
            "remote_address": "192.0.2.5",
        },
        {
            "state": "up",
            "peer_group": "PG-SPINE",
            "remote_address": "192.0.2.7",
        },
    ]

    assert STATE_MOD._is_rule_respected(rule, neighbor, all_neighbors, []) is True


def test__is_rule_respected__peer_group__above_minimum():
    """Test is_rule_respected with peer_group filter, above minimum."""
    rule = {
        "field": "peer_group",
        "contains": "PG-TOR",
        "minimum_up": 0,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "down",
        "peer_group": "PG-TOR",
        "remote_address": "192.0.2.1",
    }

    all_neighbors = [
        neighbor,
        {
            "state": "up",
            "peer_group": "PG-TOR",
            "remote_address": "192.0.2.5",
        },
        {
            "state": "up",
            "peer_group": "PG-SPINE",
            "remote_address": "192.0.2.7",
        },
    ]

    assert STATE_MOD._is_rule_respected(rule, neighbor, all_neighbors, []) is True


def test__is_rule_respected__description__below_minimum():
    """Test is_rule_respected with description filter, below minimum."""
    rule = {
        "field": "description",
        "contains": "server",
        "minimum_up": 2,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "down",
        "remote_address": "192.0.2.1",
        "description": "to:server1",
    }

    all_neighbors = [
        neighbor,
        {
            "state": "up",
            "remote_address": "192.0.2.5",
            "description": "to:server1",
        },
        {
            "state": "up",
            "remote_address": "192.0.2.7",
            "description": "to:management",
        },
    ]

    assert (
        STATE_MOD._is_rule_respected(
            rule,
            neighbor,
            all_neighbors,
            [],
        )
        is False
    )


def test__is_rule_respected__description__above_minimum():
    """Test is_rule_respected with description filter, above minimum."""
    rule = {
        "field": "description",
        "contains": "server",
        "minimum_up": 0,
        "remove_down_only": True,
    }

    neighbor = {
        "state": "down",
        "remote_address": "192.0.2.1",
        "description": "to:server1",
    }

    all_neighbors = [
        neighbor,
        {
            "state": "up",
            "remote_address": "192.0.2.5",
            "description": "to:server1",
        },
        {
            "state": "up",
            "remote_address": "192.0.2.7",
            "description": "to:server2",
        },
    ]

    assert STATE_MOD._is_rule_respected(rule, neighbor, all_neighbors, []) is True


##
# Test _is_safe_to_remove()
##


def test__is_safe_to_remove__ok(mocker):
    """Test _is_safe_to_remove() when safe."""
    mocker.patch("_states.openconfig_bgp._is_rule_respected", return_value=True)
    assert STATE_MOD._is_safe_to_remove(RULES, None, None, None) is True


def test__is_safe_to_remove__nok(mocker):
    """Test _is_safe_to_remove() when unsafe."""
    mocker.patch("_states.openconfig_bgp._is_rule_respected", side_effect=[True, False])
    assert STATE_MOD._is_safe_to_remove(RULES, None, None, None) is False
