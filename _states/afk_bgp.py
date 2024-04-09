"""States modules for AFK."""

import time


def _get_os():
    return __salt__["grains.get"]("nos", __salt__["grains.get"]("os"))


def clear_soft_all(name):
    """Execute a clear soft on all neighbors on all directions."""
    nos = _get_os()
    ret = {"name": name, "result": False, "changes": {}, "comment": ""}

    if nos == "sonic":
        time.sleep(5)  # we wait for bgp route-map delay-timer (which is set to 5 seconds)
        res = __salt__["cmd.run"]("vtysh -c 'clear bgp * soft'")
        ret["changes"]["executed"] = "vtysh -c 'clear bgp * soft"
        ret["result"] = __context__["retcode"] == 0
    elif nos == "junos":
        res = __salt__["net.cli"]("clear bgp neighbor soft all")
        ret["changes"]["executed"] = "clear bgp neighbor soft all"
        ret["result"] = res["result"]
    elif nos == "eos":
        res = __salt__["net.cli"]("clear bgp soft")
        ret["changes"]["executed"] = "clear bgp soft"
        ret["result"] = res["result"]
    else:
        raise NotImplementedError("Network OS not supported")

    ret["comment"] = res

    return ret
