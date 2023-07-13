"""Module to maintain openconfig:routing-policy.

:codeauthor: Criteo Network team
:maturity:   new
:platform:   SONiC, Arista EOS, Juniper JunOS
"""
import logging
import re

from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)


def __virtual__():
    return _get_os() in ["eos", "junos", "sonic"]


##
# Some utils
##


def _get_os():
    return __salt__["grains.get"]("nos", __salt__["grains.get"]("os"))


def _safeget(dct, *keys):
    """Safe method to get value from nested dictionary."""
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError):
            return None
    return dct


def _apply_template(template_name, context, saltenv):
    """Define a helper to generate config from template file."""
    template_content = __salt__["cp.get_file_str"](template_name, saltenv=saltenv)
    context["deep_get"] = __utils__["jinja_filters.deep_get"]

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


def _convert_range_cisco_like(mask_length_range, prefix, ipv6=False):
    """Convert openconfig range as applicable Cisco like (EOS/FRR) statement.

    TODO: migrate as either a util, or an execution module.
    """
    if mask_length_range == "exact":
        return ""
    MAX = 128 if ipv6 else 32

    current_mask = int(prefix.split("/")[1])
    mask_range = mask_length_range.split("..")
    start = int(mask_range[0])
    end = int(mask_range[1])

    if start < 0 or start > MAX or end < 0 or end > MAX:
        raise ValueError("bad range: outside of (0, {}) range".format(MAX))

    if start > end:
        raise ValueError("bad range: start cannot be higher than end")

    # 10.0.0.0/21  10..32
    if start < current_mask:
        raise ValueError("bad range: start cannot be lower than current mask")

    # 10.0.0.0/21  32..32
    if start == MAX:
        return "ge {}".format(MAX)

    # 10.0.0.0/21  21..30
    if start == current_mask:
        return "le {}".format(end)

    return "ge {} le {}".format(start, end)


def _convert_range_junos(mask_length_range, prefix, ipv6=False):
    """Convert openconfig range as applicable JunOS route-filter-list statement.

    TODO: migrate as either a util, or an execution module.
    """
    if mask_length_range == "exact":
        return "exact"

    MAX = 128 if ipv6 else 32

    current_mask = int(prefix.split("/")[1])
    mask_range = mask_length_range.split("..")
    start = int(mask_range[0])
    end = int(mask_range[1])

    if start < 0 or start > MAX or end < 0 or end > MAX:
        raise ValueError("bad range: outside of (0, {}) range".format(MAX))

    if start > end:
        raise ValueError("bad range: start cannot be higher than end")

    if start < current_mask:
        raise ValueError("bad range: start cannot be lower than current mask")

    return "prefix-length-range /{}-/{}".format(start, end)


##
# Some mapping
##


CONVERT_RANGE_MAPPING = {
    "sonic": _convert_range_cisco_like,
    "eos": _convert_range_cisco_like,
    "junos": _convert_range_junos,
}


##
# Generate community sets configuration
##


# TODO: move as util
def _get_eos_version():
    version = __salt__["grains.get"]("version")
    match = re.match(r"([0-9])+\.([0-9]+).*", version)

    if len(match.groups()) < 2:
        raise NotImplementedError("OS version not supported")

    return int(match[1]), int(match[2])


def _generate_community_set_config(community, saltenv):
    """Generate community sets configuration."""
    context = {
        "community": community["config"],
    }

    # config changes for EOS depending on its version
    suffix = ""
    nos = _get_os()
    if nos == "eos":
        major, minor = _get_eos_version()
        if major == 4 and minor < 22:
            suffix = "_before_4_22"

    return _apply_template(
        "salt://states/afk/templates/routing_policy/{}/community_set{}.j2".format(nos, suffix),
        context,
        saltenv,
    )


def _remove_community_set_config(community_name, saltenv):
    """Remove community sets configuration."""
    context = {
        "community_name": community_name,
    }

    nos = _get_os()
    return _apply_template(
        "salt://states/afk/templates/routing_policy/{}/remove_community_set.j2".format(nos),
        context,
        saltenv,
    )


def _generate_communities_config(openconfig, existing_community_lists, saltenv):
    """Generate community sets configuration."""
    config = []

    for community_set in openconfig["community-set"]:
        # remove the community-set to ensure no extra config nor sequence
        if (
            _get_os() != "sonic"
            or community_set["config"]["community-set-name"] in existing_community_lists
        ):
            config.append(
                _remove_community_set_config(community_set["config"]["community-set-name"], saltenv)
            )
        config.append(_generate_community_set_config(community_set, saltenv))

    return config


##
# Generate prefix sets configuration
##


def _generate_prefix_set_config(prefix_set, saltenv):
    """Generate prefix sets configuration."""
    context = {
        "prefix_set_name": prefix_set["config"]["name"],
        "prefix_set_mode": prefix_set["config"]["mode"],
        "prefixes": prefix_set["prefixes"]["prefix"],
        # TODO: do the for loop in python and not in jinja, and enrich at this moment
        # currently: the easiest and most efficient way
        "convert_range": CONVERT_RANGE_MAPPING[_get_os()],
    }

    nos = _get_os()
    return _apply_template(
        "salt://states/afk/templates/routing_policy/{}/prefix_set.j2".format(nos), context, saltenv
    )


def _remove_prefix_set_config(prefix_set_name, prefix_set_mode, saltenv):
    """Remove prefix sets configuration."""
    context = {
        "prefix_set_name": prefix_set_name,
        "prefix_set_mode": prefix_set_mode,
    }

    nos = _get_os()
    return _apply_template(
        "salt://states/afk/templates/routing_policy/{}/remove_prefix_set.j2".format(nos),
        context,
        saltenv,
    )


def _generate_prefix_sets_config(openconfig, existing_objects, saltenv):
    """Generate prefix sets configuration."""
    config = []
    prefixes_set_mode = {}

    for prefix_set in openconfig["prefix-set"]:
        if prefix_set["config"]["mode"] == "IPV4":
            existing_prefix_lists = existing_objects.get("ipv4_prefix_lists", {})
        else:
            existing_prefix_lists = existing_objects.get("ipv6_prefix_lists", {})

        # remove the prefix set to clean all sequence
        if _get_os() != "sonic" or prefix_set["config"]["name"] in existing_prefix_lists:
            config.append(
                _remove_prefix_set_config(
                    prefix_set["config"]["name"], prefix_set["config"]["mode"], saltenv
                )
            )

        # extracting the IP version of each prefix-list for usage in policies
        prefixes_set_mode[prefix_set["config"]["name"]] = prefix_set["config"]["mode"]

        prefix_set_config = _generate_prefix_set_config(prefix_set, saltenv)
        config.append(prefix_set_config)

    return config, prefixes_set_mode


##
# Policy dependency checks
##


def _is_prefix_set_declared(prefix_set_name, defined_sets):
    """Ensure the prefix-set exists."""
    try:
        for prefix in defined_sets["prefix-sets"]["prefix-set"]:
            if prefix["config"]["name"] == prefix_set_name:
                return True
        return False
    except KeyError:
        return False


def _is_community_set_declared(community_set_name, defined_sets):
    """Ensure the community-set exists."""
    try:
        for community in defined_sets["bgp-defined-sets"]["community-sets"]["community-set"]:
            if community["config"]["community-set-name"] == community_set_name:
                return True
        return False
    except KeyError:
        return False


##
# Generate policy configuration
##


def _generate_statement_config(route_map_name, afisafis, statement, prefixes_set_mode, saltenv):
    """Generate statement configuration."""
    context = {
        "route_map_name": route_map_name,
        "afisafis": afisafis,
        "sequence": statement["name"],
        "actions": statement["actions"],
        "conditions": statement.get("conditions"),
        "prefixes_set_mode": prefixes_set_mode,
        "convert_route_map_name": __utils__["jinja_filters.format_route_policy_name"],
    }

    nos = _get_os()
    return _apply_template(
        "salt://states/afk/templates/routing_policy/{}/statement.j2".format(nos), context, saltenv
    )


def _remove_route_policy_config(route_map_name, saltenv):
    """Remove route policy configuration."""
    context = {
        "route_map_name": route_map_name,
        "convert_route_map_name": __utils__["jinja_filters.format_route_policy_name"],
    }

    nos = _get_os()
    return _apply_template(
        "salt://states/afk/templates/routing_policy/{}/remove_policy.j2".format(nos),
        context,
        saltenv,
    )


def _generate_policies_config(
    openconfig, rp_afisafis_mapping, prefixes_set_mode, defined_sets, existing_route_maps, saltenv
):
    """Generate routing policies configuration."""
    config = []

    for policies in openconfig["policy-definition"]:
        # remove the route-map to ensure no extra config nor sequence
        if _get_os() != "sonic" or policies["config"]["name"] in existing_route_maps:
            config.append(_remove_route_policy_config(policies["config"]["name"], saltenv))

        for statement in policies["statements"]["statement"]:
            prefix_set_name = _safeget(
                statement, "conditions", "match-prefix-set", "config", "prefix-set"
            )
            if prefix_set_name and not _is_prefix_set_declared(prefix_set_name, defined_sets):
                raise ValueError("Declared prefix-list does not exist: {}".format(prefix_set_name))

            community_set_name = _safeget(
                statement, "conditions", "bgp-conditions", "config", "community-set"
            )
            if community_set_name and not _is_community_set_declared(
                community_set_name, defined_sets
            ):
                raise ValueError("Declared community does not exist: {}".format(community_set_name))

            policy_name = policies["config"]["name"]
            policy_config = _generate_statement_config(
                policy_name,
                rp_afisafis_mapping.get(policy_name),
                statement,
                prefixes_set_mode,
                saltenv,
            )
            config.append(policy_config)

    return config


def _get_route_policies_empty_set(route_policies):
    return {route_policy["config"]["name"]: set([""]) for route_policy in route_policies}


def _get_route_policy_afi_safis_usage(route_policies, bgp):
    """Return a dict of route policies and a set of AFI/SAFIS.

    There will always be an empty value to also set the original route-policy
    for JunOS, because for it we generate also duplicate route-policies with adding
    a filter on the SAFI.

    {
        "RM-TEST": set("", "IPV4_UNICAST", "IPV6_UNICAST"),
        "RM-LAN-IN": set("", "IPV4_UNICAST")
    }
    """
    # We get all the route_policies name
    route_policies_set = _get_route_policies_empty_set(route_policies["policy-definition"])
    for neighbor in bgp["neighbors"]["neighbor"]:
        for afisafi in neighbor["afi-safis"]["afi-safi"]:
            if not afisafi.get("apply-policy"):
                continue
            for policy_name in afisafi["apply-policy"]["config"]["import-policy"]:
                route_policies_set[policy_name].add(afisafi["afi-safi-name"])
            for policy_name in afisafi["apply-policy"]["config"]["export-policy"]:
                route_policies_set[policy_name].add(afisafi["afi-safi-name"])
    return route_policies_set


##
# Main code
##


def _generate_routing_policy_config(openconfig_routing_policy, openconfig_bgp, _, saltenv):
    # TODO: handle when no data
    # TODO: add safeguards
    # TODO: generalize this to all OS to be able to remove extra objects)
    #   Removing extras is only support for SONiC for now
    #   extract items from the config (prefix list, community list etc...)
    #   it will be used in templates to clean objects needing changes
    existing_assets = {}
    if _get_os() == "sonic":
        current_config = __salt__["sonic.get_bgp_config"]()
        existing_assets = __utils__["frr_detect_diff.get_objects"](current_config)

    rp_afisafis_mapping = {}
    if _get_os() == "junos":
        # For JunOS, we need to know where are used the route policies, to auto generate a
        # route policy for each AFI/SAFI the route policy is used
        rp_afisafis_mapping = _get_route_policy_afi_safis_usage(
            openconfig_routing_policy["policy-definitions"], openconfig_bgp
        )

    prefix_set, prefixes_set_mode = _generate_prefix_sets_config(
        openconfig_routing_policy["defined-sets"]["prefix-sets"], existing_assets, saltenv
    )
    community_sets = _generate_communities_config(
        openconfig_routing_policy["defined-sets"]["bgp-defined-sets"]["community-sets"],
        existing_assets.get("community_lists", {}),
        saltenv,
    )
    policy_definitions = _generate_policies_config(
        openconfig_routing_policy["policy-definitions"],
        rp_afisafis_mapping,
        prefixes_set_mode,
        openconfig_routing_policy["defined-sets"],
        existing_assets.get("route_maps", {}),
        saltenv,
    )

    # assemble the routing_policy configuration
    context = {
        "community_sets": community_sets,
        "prefix_sets": prefix_set,
        "policy_definitions": policy_definitions,
    }

    nos = _get_os()
    config = _apply_template(
        "salt://states/afk/templates/routing_policy/{}/routing_policy.j2".format(nos),
        context,
        saltenv,
    )

    log.debug("generated config parts: %s", config)

    return config


def apply(name, openconfig_routing_policy=None, openconfig_bgp=None, saltenv="base"):
    """Apply and maintain Routing Policies configuration from openconfig format (JSON is expected).

    .. warning::
        Be careful with dry run, in some conditions napalm apply the config instead of
        discarding it.
        Did not find the root cause yet.

    :param name: name of the task
    :param openconfig_routing_policy: Routing Policy configuration in JSON in openconfig
        (routing-policy)
    :param openconfig_bgp: BGP configuration in JSON in openconfig (bgp)
    :param saltenv: salt environment
    """
    ret = {"name": name, "result": False, "changes": {}, "comment": ""}

    # generate command to apply on the device using the templates
    log.debug("%s starting", name)

    # get candidate config
    config = _generate_routing_policy_config(
        openconfig_routing_policy, openconfig_bgp, False, saltenv
    )

    nos = _get_os()

    if nos in ["eos", "junos"]:
        # only return generated commands/config during tests
        # there is an ongoing bug with napalm making dry-run really applying the config sometimes
        if __opts__["test"]:
            ret["changes"] = {"gen": config}
            ret["result"] = None
            return ret

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
            push_only_if_changes=True,
            test=__opts__["test"],
        )
        res["diff"] = res["changes"]

    ret["comment"] = res["comment"]
    ret["changes"] = {"diff": res["diff"], "loaded": config}
    ret["result"] = res["result"]

    return ret
