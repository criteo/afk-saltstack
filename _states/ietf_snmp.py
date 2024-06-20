"""Module to maintain ietf:snmp.

:codeauthor: Criteo Network team
:maturity:   new
:platform:   SONiC, Arista EOS, Juniper JunOS
"""

import logging

from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)


##
# Some utils
##


def __virtual__():
    return _get_os() in ["eos", "junos", "sonic"]


def _get_os():
    return __salt__["grains.get"]("nos", __salt__["grains.get"]("os"))


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


def _generate_snmp_config(ietf, _, saltenv):
    # TODO: handle when no data
    os = _get_os()
    config = _apply_template(
        "salt://states/afk/templates/snmp/{}/snmp.j2".format(os),
        ietf,
        saltenv,
    )

    return config


def apply(name, ietf_config=None, saltenv="base"):
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
    ret = {"name": name, "result": False, "changes": {}, "comment": []}

    # generate command to apply on the device using the templates
    log.debug("%s starting", name)

    if not ietf_config:
        ret["comment"].append("No configuration provided")
        return ret

    nos = _get_os()

    if nos in ["eos", "junos"]:
        # only return generated commands/config during tests
        # there is an ongoing bug with napalm making dry-run really applying the config sometimes
        config = _generate_snmp_config(ietf_config, False, saltenv)

        if __opts__["test"]:
            ret["result"] = None
            return ret

        res = __salt__["net.load_config"](
            text=config,
            test=__opts__["test"],
            debug=True,
        )
        ret["comment"].append("- loaded:\n{}".format(config))

    elif nos == "sonic":
        res = __salt__["sonic.snmp_config"](
            template_name="salt://states/afk/templates/snmp/{}/snmp.j2".format(nos),
            saltenv=saltenv,
            context=ietf_config,
            test=__opts__["test"],
        )
        res["diff"] = res["changes"]

    ret["comment"].append(res["comment"])
    if res["diff"]:
        ret["changes"] = {"diff": res["diff"]}
    ret["result"] = res["result"]

    return ret
