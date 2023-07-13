"""Module to maintain openconfig:bgp.

:codeauthor: Criteo Network team
:maturity:   new
:platform:   SONiC, Arista EOS, Juniper JunOS
"""
import logging
import re
from collections import defaultdict
from enum import Enum
from ipaddress import ip_address

from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

SAFIS_ALIAS = {
    "eos": {
        "IPV4_UNICAST": "ipv4",
        "IPV6_UNICAST": "ipv6",
    },
    "sonic": {
        "IPV4_UNICAST": "ipv4 unicast",
        "IPV6_UNICAST": "ipv6 unicast",
    },
    "junos": {
        "IPV4_UNICAST": "inet unicast",
        "IPV6_UNICAST": "inet6 unicast",
    },
}

# to map the afi-safi-name with the key of the container in openconfig tree
SAFI_MAPPING_OPENCONFIG = {
    "IPV4_UNICAST": "ipv4-unicast",
    "IPV6_UNICAST": "ipv6-unicast",
}


class SafiAssetType(Enum):
    """Enum to define the type of asset."""

    PEER_GROUP = "peer-group"
    NEIGHBOR = "neighbor"


def __virtual__():
    return _get_os() in ["eos", "sonic", "junos"]


##
# Some utils
##


def _get_os():
    return __salt__["grains.get"]("nos", __salt__["grains.get"]("os"))


def _apply_template(template_name, context, saltenv):
    """Define a helper to generate config from template file."""
    template_content = __salt__["cp.get_file_str"](template_name, saltenv=saltenv)

    if not template_content:
        raise CommandExecutionError("Unable to get {}".format(template_name))

    result = __salt__["file.apply_template_on_contents"](
        contents=template_content,
        template="jinja",
        context=context,
        defaults=None,
        saltenv=saltenv,
    )

    return "\n".join([line for line in result.splitlines() if line.strip() != ""])


##
# Generate global configuration
##


def _generate_global_conf_part(config, saltenv):
    """Generate global configuration part."""
    if not config:
        return ""

    nos = _get_os()
    default_vrf = __salt__["pillar.get"]("vrf", {}).get("default", "")

    context = {
        "config": config,
        "vrf": default_vrf,  # TODO: add VRF support
    }

    template = "salt://states/afk/templates/bgp/{}/global_configuration.j2".format(nos)

    return _apply_template(template, context, saltenv)


def _get_administrative_distance(global_conf):
    bgp_distance = {}

    try:
        bgp_distance["external"] = global_conf["default-route-distance"]["config"][
            "external-route-distance"
        ]
    except KeyError:
        pass

    try:
        bgp_distance["internal"] = global_conf["default-route-distance"]["config"][
            "internal-route-distance"
        ]
    except KeyError:
        pass

    return bgp_distance


def _get_global_as(openconfig, nos):
    """Get global AS from current or expected config."""
    current_global_as = __salt__["criteo_bgp.get_global_as"](vrf="default")
    expected_global_as = openconfig.get("global", {}).get("config", {}).get("as", "")

    if nos != "junos" and not current_global_as and not expected_global_as:
        raise CommandExecutionError("No Global AS found in both current and expected config")

    if current_global_as and expected_global_as and current_global_as != expected_global_as:
        raise CommandExecutionError(
            "Global AS different between current and expected config, manual migration required"
        )

    return expected_global_as or current_global_as


##
# Generate peer groups
##


# TODO: factorize => move as util
def _get_eos_version():
    version = __salt__["grains.get"]("version")
    match = re.match(r"([0-9])+\.([0-9]+).*", version)

    if len(match.groups()) < 2:
        raise NotImplementedError("OS version not supported")

    return int(match[1]), int(match[2])


def _generate_peer_group_part(peer_group, prefix_limit_config, bgp_distance, saltenv):
    """Generate peer-group configuration part."""
    nos = _get_os()
    default_vrf = __salt__["pillar.get"]("vrf", {}).get("default", "")
    context = {
        "peer_group": peer_group,
        "vrf": default_vrf,  # TODO: add VRF support
        "prefix_limit_config": prefix_limit_config,
        "bgp_distance": bgp_distance,
    }
    nos = _get_os()

    # config changes for EOS depending on its version
    suffix = ""
    nos = _get_os()
    if nos == "eos":
        major, minor = _get_eos_version()
        if major == 4 and minor < 22:
            suffix = "_before_4_22"

    template = "salt://states/afk/templates/bgp/{}/peer_group{}.j2".format(nos, suffix)

    return _apply_template(template, context, saltenv)


def _generate_peer_group(peer_group, bgp_distance, saltenv):
    # extract parameters from openconfig peer group tree
    safis, prefix_limit_config = _get_safi_params(peer_group)

    # generate safi config for the peer group
    safis_config = {}
    safis_config["IPV4_UNICAST"] = _generate_safi_part(
        "IPV4_UNICAST", safis.get("IPV4_UNICAST", {}), peer_group, SafiAssetType.PEER_GROUP, saltenv
    )
    safis_config["IPV6_UNICAST"] = _generate_safi_part(
        "IPV6_UNICAST", safis.get("IPV6_UNICAST", {}), peer_group, SafiAssetType.PEER_GROUP, saltenv
    )

    peer_group_config = _generate_peer_group_part(
        peer_group, prefix_limit_config, bgp_distance, saltenv
    )

    return peer_group_config, safis_config


##
# Generate sessions
##


def _generate_neighbor_part(
    neighbor, global_as, prefix_limit_config, bgp_distance, peer_groups, saltenv
):
    """Generate neighbor configuration part."""
    default_vrf = __salt__["pillar.get"]("vrf", {}).get("default", "")
    current_bgp_config = __salt__["criteo_bgp.get_neighbors"](dict_per_address=True).get(
        "result", {}
    )
    context = {
        "neighbor": neighbor,
        "global_as": global_as,
        "vrf": default_vrf,  # TODO: add VRF support
        "prefix_limit_config": prefix_limit_config,
        "bgp_distance": bgp_distance,
        "current_config": current_bgp_config,
        "peer_groups": peer_groups,
    }

    nos = _get_os()
    template = "salt://states/afk/templates/bgp/{}/neighbor.j2".format(nos)

    return _apply_template(template, context, saltenv)


def _get_global_route_maps(asset):
    """Extract global route-map set for the neighbor/peer-group.

    Mandatory to fallback on global-route-map on FRR, as it does not permit to have a
    route-map set on a neighbor/peer-group outside a SAFI. So the fallback logic is handled
    in the template.
    """
    global_route_map = {"import": None, "export": None}
    try:
        global_route_map["import"] = asset["apply-policy"]["config"]["import-policy"]
    except KeyError:
        pass

    try:
        global_route_map["export"] = asset["apply-policy"]["config"]["export-policy"]
    except KeyError:
        pass

    return global_route_map


def _generate_safi_part(safi_name, params, asset, asset_type, saltenv):
    """Generate SAFI configuration part."""
    nos = _get_os()
    default_vrf = __salt__["pillar.get"]("vrf", {}).get("default", "")
    # TODO: rework context by sending both neighbor and safi information directly
    context = {
        "asset_type": asset_type.value,
        "vrf": default_vrf,  # TODO: add VRF support
        "safi": params,
        "safi_name": SAFIS_ALIAS[nos][safi_name],
        "safi_key": SAFI_MAPPING_OPENCONFIG[safi_name],
        "convert_route_map_name": __utils__["jinja_filters.format_route_policy_name"],
    }

    # add parameters when setting neighbor/peer-group
    if asset_type == SafiAssetType.NEIGHBOR:
        context["neighbor"] = {
            "address": asset["neighbor-address"],
            "peer_group": asset["config"].get("peer-group"),
        }
    elif asset_type == SafiAssetType.PEER_GROUP:
        context["peer_group"] = asset

    # getting global route-maps (see docstring of _get_global_route_maps)
    context["global_route_map"] = _get_global_route_maps(asset)

    template = "salt://states/afk/templates/bgp/{}/safi.j2".format(nos)

    return _apply_template(template, context, saltenv)


def _get_safi_params(asset):
    """Extract parameters from openconfig neighbor/peer-group tree."""
    safis = {}
    prefix_limit_config = None

    if "afi-safis" not in asset or "afi-safi" not in asset["afi-safis"]:
        return safis, prefix_limit_config

    # extract infos and index SAFIS
    for safi in asset["afi-safis"]["afi-safi"]:
        # index SAFIS to ease usage in template
        safis[safi["afi-safi-name"]] = safi

        # find the safi of the neighbor to extract the maximum prefix
        # in EOS, maximum prefixes are not set in a SAFI
        safi_key = SAFI_MAPPING_OPENCONFIG[safi["afi-safi-name"]]
        try:
            safi_prefix_limit_config = safi[safi_key]["prefix-limit"]["config"]
            if safi_prefix_limit_config:
                prefix_limit_config = safi_prefix_limit_config
        except KeyError:
            pass

    return safis, prefix_limit_config


def _generate_neighbor_config(neighbor, global_as, bgp_distance, peer_groups, saltenv):
    """Generate the entire configuration for a neighbor."""
    # extract parameters from openconfig neighbor tree
    safis, prefix_limit_config = _get_safi_params(neighbor)

    # generate neighbor config
    neighbor_config = _generate_neighbor_part(
        neighbor, global_as, prefix_limit_config, bgp_distance, peer_groups, saltenv
    )

    # generate safi config for the neighbor
    safis_config = {}
    safis_config["IPV4_UNICAST"] = _generate_safi_part(
        "IPV4_UNICAST", safis.get("IPV4_UNICAST", {}), neighbor, SafiAssetType.NEIGHBOR, saltenv
    )
    safis_config["IPV6_UNICAST"] = _generate_safi_part(
        "IPV6_UNICAST", safis.get("IPV6_UNICAST", {}), neighbor, SafiAssetType.NEIGHBOR, saltenv
    )

    return (neighbor_config, safis_config)


##
# Remove unwanted sessions
##


def _is_rule_respected(rule, neighbor, all_neighbors, neighbors_to_remove):
    # if the neighbor is not concerned by the rule, we ignore the rule
    if rule["contains"] not in neighbor[rule["field"]]:
        return True

    # we authorize removing down neighbor only
    if rule.get("remove_down_only") and neighbor["state"] == "up":
        return False

    afi = ip_address(neighbor["remote_address"]).version

    nb_matching_neighbors = 0
    for existing_neighbor in all_neighbors:
        # check if the existing neighbor is matching the rule
        if rule["contains"] not in existing_neighbor[rule["field"]]:
            continue

        # consider only neighbors in the same AFI than the neighbor to remove
        if ip_address(existing_neighbor["remote_address"]).version != afi:
            continue

        # consider only up BGP session
        if existing_neighbor["state"] != "up":
            continue

        # exclude the session already planned to be removed
        if existing_neighbor in neighbors_to_remove:
            continue

        # exclude the neighbor to remove to check if there will be enough resilience afterwards
        if existing_neighbor == neighbor:
            continue

        nb_matching_neighbors += 1

    return nb_matching_neighbors >= rule["minimum_up"]


def _is_safe_to_remove(rules, neighbor, all_neighbors, neighbors_to_remove):
    """Check if neighbor can be removed safely according user defined rules.

    The rules are set in a pillar.

    The element checked can be: description or peer_group

    It can check a minimum of up neighbor to respect, taking into account neighbors already marked
    as to remove.

    We can forbid removing up neighbors. It could help force removing BGP on uplink before removing
    the matching session on the neighbor downlink.

    .. note::
        bgp_removal_safeguards:
            by_peer_group:
              - field: "peer_group"
                contains: "PG-TOR"
                minimum_up: 2
                remove_down_only: true
            by_description:
              - field: "description"
                contains: "server"
                minimum_up: 2
                remove_down_only: false

    :param neighbor: neighbor detail from criteo_bgp.get_neighbors
    """
    if not rules:
        return True

    for rule in rules:
        if not _is_rule_respected(rule, neighbor, all_neighbors, neighbors_to_remove):
            return False

    return True


def _get_unwanted_neighbors(neighbors, rules):
    """Get unwanted installed neighbors."""
    # get BGP sessions on the device
    installed_neighbors = __salt__["criteo_bgp.get_neighbors"]().get("result")

    # get unwanted bgp sessions
    wanted_neighbors = [neighbor["neighbor-address"] for neighbor in neighbors]
    unwanted_neighbors = []

    for neighbor in installed_neighbors:
        if neighbor["remote_address"] not in wanted_neighbors and _is_safe_to_remove(
            rules, neighbor, installed_neighbors, unwanted_neighbors
        ):
            unwanted_neighbors.append(neighbor)

    return unwanted_neighbors


def _remove_neighbor_config(neighbors, rules, saltenv):
    """Remove BGP neighbors on the device but not in openconfig."""
    context = {"unwanted_neighbors": _get_unwanted_neighbors(neighbors, rules)}
    nos = _get_os()

    # generate the command to remove them
    return _apply_template(
        "salt://states/afk/templates/bgp/{}/neighbor_removal.j2".format(nos), context, saltenv
    )


##
# Main code
##


def _generate_bgp_config(openconfig, remove_extras, rules, saltenv):  # pylint: disable=R0914
    """Generate the BGP configuration."""
    # TODO: in CMDB, when done remove the "# pylint: disable=R0914"
    nos = _get_os()

    peer_group_configs = []
    neighbor_configs = []
    safi_configs = defaultdict(list)

    # generate global configuration
    # TODO: in python, detect mistmatch between expected router as and current as!
    global_as = _get_global_as(openconfig, nos)
    global_conf = _generate_global_conf_part(openconfig.get("global"), saltenv)
    bgp_distance = _get_administrative_distance(openconfig.get("global", {}))

    # generate configuration for all peer groups
    peer_groups = {}
    for peer_group in openconfig.get("peer-groups", {}).get("peer-group", {}):
        peer_groups[peer_group["peer-group-name"]] = peer_group
        peer_group_config, safi_config = _generate_peer_group(peer_group, bgp_distance, saltenv)
        peer_group_configs.append(peer_group_config)

        # we merge config per safi
        for _safi, _config in safi_config.items():
            safi_name = SAFIS_ALIAS[nos][_safi]
            safi_configs[safi_name].append(_config)

    # generate configuration for all neighbors and safis
    for neighbor in openconfig["neighbors"]["neighbor"]:
        neighbor_config, safi_config = _generate_neighbor_config(
            neighbor, global_as, bgp_distance, peer_groups, saltenv
        )
        neighbor_configs.append(neighbor_config)

        # we merge config per safi
        for _safi, _config in safi_config.items():
            safi_name = SAFIS_ALIAS[nos][_safi]
            safi_configs[safi_name].append(_config)

    # generate configuration to remove unwanted bgp sessions
    neighbors_to_remove = []
    if remove_extras:
        neighbors_to_remove = _remove_neighbor_config(
            openconfig["neighbors"]["neighbor"], rules, saltenv
        )

    # assemble the BGP configuration
    context = {
        "global_as": global_as,
        "global_configuration": global_conf,
        "peer_groups": peer_group_configs,
        "neighbors": neighbor_configs,
        "neighbors_to_remove": neighbors_to_remove,
        "safis": safi_configs,
    }

    template = "salt://states/afk/templates/bgp/{}/bgp.j2".format(nos)

    config = _apply_template(template, context, saltenv)

    log.debug("generated config parts: %s", config)

    return config


def apply(name, openconfig=None, remove_extras=False, rules=None, saltenv="base"):
    """Apply and maintain BGP configuration from openconfig format (JSON is expected).

    .. warning::
        Be careful with dry run, in some conditions napalm apply the config instead of
        discarding it.
        Did not find the root cause yet.

    .. note::
        supported: EOS and SONiC
        JunOS support is coming.

    :param name: name of the task
    :param openconfig: network BGP configuration in JSON in openconfig structure (openconfig:bgp)
    :param remove_extras: remove unwanted installed BGP sessions
    :param saltenv: salt environment
    """
    ret = {"name": name, "result": False, "changes": {}, "comment": ""}

    # generate command to apply on the device using the templates
    log.debug("%s starting", name)
    config = _generate_bgp_config(openconfig, remove_extras, rules, saltenv)

    # only return generated commands/config during tests
    # there is an ongoing bug with napalm making dry-run really applying the config sometimes
    if __opts__["test"]:
        ret["changes"] = {"gen": config}
        ret["result"] = None
        return ret

    nos = _get_os()

    if nos in ["eos", "junos"]:
        res = __salt__["net.load_config"](
            text=config,
            test=__opts__["test"],
            debug=True,
        )
    elif nos == "sonic":
        # TODO: modify .managed to support pushing raw config without template
        res = __salt__["sonic.bgp_config"](
            template_name="salt://templates/dummy.j2",
            context={"raw": config},
            test=__opts__["test"],
        )
        res["diff"] = res["changes"]

    ret["comment"] = res["comment"]
    ret["changes"] = {"diff": res["diff"], "loaded": config}
    ret["result"] = res["result"]

    return ret
