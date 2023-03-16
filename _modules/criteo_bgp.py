"""Agnostic BGP module to retrieve information.

:codeauthor: Criteo Network team
:maturity:   new
:platform:   SONiC, Arista EOS, Juniper JunOS
"""
import json
from ipaddress import ip_address, ip_interface


def _get_os():
    return __salt__["grains.get"]("nos", __salt__["grains.get"]("os"))


def get_global_as(vrf="default"):
    """Get global AS of the defined VRF.

    Only EOS and SONiC are supported (it does not make sense on Juniper).

    :param vrf: routing instance

    CLI Example:

    .. code-block:: bash

        salt "tor1.dc1" criteo_bgp.get_global_as

    .. code-block:: python

        {'tor1.dc1': 65001}
    """
    nos = _get_os()
    result = None
    if nos == "eos":
        command = "show ip bgp summary vrf {}".format(vrf)
        bgp_sum = __salt__["napalm.pyeapi_run_commands"](command)
        result = bgp_sum[0]["vrfs"].get(vrf, {}).get("asn", "unknown")

    if nos == "sonic":
        bgp_sum = __salt__["cmd.run"]("vtysh -c 'show bgp json'")
        result = json.loads(bgp_sum).get("localAS")

    return result


def _junos_peer_group_mapping():
    # get the group name using the group index get-bgp-group-information detail
    # this method works for junos >= 14.1
    rpc_results = __salt__["napalm.junos_rpc"](
        "get-bgp-group-information",
        format="xml",
    )
    group_info = rpc_results["out"]

    if isinstance(group_info["bgp-group-information"]["bgp-group"], list):
        groups = group_info["bgp-group-information"]["bgp-group"]
    else:
        # if only one group, it is not a list
        groups = [group_info["bgp-group-information"]["bgp-group"]]

    # if multiple groups, it is a list
    return {x["group-index"]: x["name"] for x in groups}


def _junos_extra_info():
    result = {}
    group_resolution_needed = False

    rpc_results = __salt__["napalm.junos_rpc"]("get-bgp-neighbor-information", format="xml")
    peers = rpc_results["out"].get("bgp-information", {}).get("bgp-peer", {})

    for peer in peers:
        # cleaning remote address exposed in RPC, example: 192.0.2.0+58771 => 192.0.2.0
        remote = peer["peer-address"].split("+")[0]

        result[remote] = {}

        if "description" in peer:
            result[remote]["description"] = peer["description"]

        if "peer-group" in peer:
            result[remote]["peer-group"] = peer["peer-group"]
        elif "group-index" in peer:
            group_resolution_needed = True
            result[remote]["group-index"] = peer["group-index"]

    if group_resolution_needed:
        map_peer_group = _junos_peer_group_mapping()
        for peer, info in result.items():
            if not info.get("group-index"):
                continue

            info["peer-group"] = map_peer_group[info["group-index"]]

    return result


def _eos_extra_info():
    result = {}
    bgp_config = __salt__["bgp.config"]()["out"]

    for peer_group_name, group_info in bgp_config.items():
        for remote, peer_info in group_info.get("neighbors", {}).items():
            peer_group_name = None if peer_group_name == "_" else peer_group_name
            result[remote] = {
                "peer-group": peer_group_name,
                "description": peer_info.get("description"),
            }

    return result


def get_bgp_extra_info():
    """Get extra information for BGP session like peer-group and description.

    Useful only for NOS not exposing data directly in the "show bgp neighbor" result: JunOS and EOS.

    CLI Example:

    .. code-block:: bash

        salt "spine1.dc1" criteo_bgp.get_bgp_extra_info

    .. code-block:: python

        {
            "spine1.dc1": {
                "192.0.2.0": {
                    "description": "VAL:PG-TOR:tor1.dc1",
                    "peer-group": "PG-TOR"
                },
                "192.0.2.2": {
                    "description": "VAL:PG-TOR:tor2.dc1",
                    "peer-group": "PG-TOR"
                },
                "192.0.2.4": {
                    "description": "VAL:PG-TOR:tor3.dc1",
                    "peer-group": "PG-TOR"
                }
        }

    """
    nos = _get_os()

    if nos == "junos":
        return _junos_extra_info()

    if nos == "eos":
        return _eos_extra_info()

    raise NotImplementedError("Unsupported network OS.")


def get_route_map_list():
    """Get list of route-map installed on the device.

    CLI Example:

    .. code-block:: bash

        salt "super.spine1.dc1" criteo_bgp.get_route_map_list

    .. code-block:: python

        [
            "PFE-LB",
            "RM-LAN-IN",
            "RM-LAN-OUT",
            "RM-LAN_MAINTENANCE-OUT",
            "RM-LAN_MAINTENANCE_DEFAULT-OUT",
            "RM-DENY",
        ]
    """
    nos = _get_os()
    rm_list = None
    if nos == "junos":
        # xml rpc of "show policy" is not available
        output = __salt__["net.cli"]("show policy")
        raw_res = output.get("out", {}).get("show policy", "")

        separator = "\n" if "\n" in raw_res else ""
        raw_list = raw_res.replace("Configured policies:", "").split(separator)

        # filter the route-map list
        rm_list = [rm for rm in raw_list if rm != ""]
    elif nos == "eos":
        output = __salt__["napalm.rpc"]("show route-map")
        rm_list = list(output[0]["routeMaps"].keys())
    elif nos == "sonic":
        rm_list = __salt__["sonic.get_route_maps"]()
    else:
        raise NotImplementedError("OS '{}' not supported".format(nos))

    return rm_list


def _bgp_neighbor_napalm(local_network=None):
    """Get and parse BGP info from Napalm device."""
    bgp = []
    bgp_neighbors = __salt__["bgp.neighbors"]()["out"]
    bgp_extra_info = get_bgp_extra_info()
    for vrf, autonomous_system in bgp_neighbors.items():
        for remote_as, neighbors in autonomous_system.items():
            for session in neighbors:
                remote_address = ip_address(session["remote_address"])
                state = "up" if session["up"] else "down"

                if not local_network or remote_address in local_network:
                    neighbor_extra = bgp_extra_info.get(session["remote_address"], {})
                    bgp.append(
                        {
                            "remote_as": remote_as,
                            "local_as": session["local_as"],
                            "remote_address": session["remote_address"],
                            "vrf": vrf,
                            "export_policy": session["export_policy"],
                            "import_policy": session["import_policy"],
                            "peer_group": neighbor_extra.get("peer-group"),
                            "description": neighbor_extra.get("description"),
                            "state": state,
                        }
                    )
    return bgp


def _bgp_neighbor_sonic(local_network=None):
    """Get and parse BGP info from SONiC device."""
    bgp = []
    bgp_neighbors = __salt__["sonic.get_bgp_neighbors"]()
    for session in bgp_neighbors.values():
        remote_address = ip_address(session["remote_address"])
        if not local_network or remote_address in local_network:
            bgp.append(session)

    return bgp


def get_neighbors(local_cidr=None, dict_per_address=False):
    """Get bgp neighbors from CIDR.

    :param cidr: CIDR, can be whether a real network address, or host (example: 192.168.0.0/30)
    :param dict_per_address: return a dict with neighbor address as a key, instead of a list

    CLI Example:

    .. code-block:: bash

        salt "super.spine1.dc1" criteo_bgp.get_neighbors 10.0.0.129/31

    Output example:

    .. code-block:: python

        {
            "result": [
                {
                    "remote_as": 65502,
                    "local_as": 65000,
                    "remote_address": "10.0.0.128",
                    "vrf": "prod",
                    "export_policy": "RM-LAN-OUT",
                    "import_policy": "RM-LAN-IN",
                    "peer_group": "PG-SPINE",
                    "description": "NMO:NEIGHBOR",
                    "state": "up",
                }
            ]
        }
    """
    local_network = ip_interface(local_cidr).network if local_cidr else None
    func = {
        "sonic": _bgp_neighbor_sonic,
        "eos": _bgp_neighbor_napalm,
        "junos": _bgp_neighbor_napalm,
    }
    nos = _get_os()
    bgp = func[nos](local_network)

    if dict_per_address:
        result = {}
        for neighbor in bgp:
            result[neighbor["remote_address"]] = neighbor
        bgp = result

    return {"result": bgp}
