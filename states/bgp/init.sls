bgp_sessions:
    openconfig_bgp.apply:
        - openconfig: {{ pillar["openconfig"]["bgp"] | yaml }}