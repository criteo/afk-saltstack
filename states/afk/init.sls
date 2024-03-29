route_policies:
    openconfig_routing_policy.apply:
        - openconfig_routing_policy: {{ pillar["openconfig"]["routing-policy"] | yaml }}
        - openconfig_bgp: {{ pillar["openconfig"]["network-instances"]["network-instance"][0]["protocols"]["protocol"][0]["bgp"] | yaml }}
        - saltenv: {{ saltenv }}

bgp_sessions:
    openconfig_bgp.apply:
        - openconfig: {{ pillar["openconfig"]["network-instances"]["network-instance"][0]["protocols"]["protocol"][0]["bgp"] | yaml }}
        - require:
            - openconfig_routing_policy: route_policies
        - saltenv: {{ saltenv }}

clear_bgp_soft:
    afk_bgp.clear_soft_all:
        - onchanges:
            - openconfig_bgp: bgp_sessions
            - openconfig_routing_policy: route_policies
