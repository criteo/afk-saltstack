route_policies:
    openconfig_routing_policy.apply:
        - openconfig_routing_policy: {{ pillar["openconfig"]["routing-policy"] | yaml }}
        - openconfig_bgp: {{ pillar["openconfig"]["bgp"] | yaml }}
