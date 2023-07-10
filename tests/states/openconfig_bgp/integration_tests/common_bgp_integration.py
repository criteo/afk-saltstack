import json


def assert_expected_integration_result(scenario, os_name):
    """Get data and compare to expected results."""
    test_path = "tests/states/openconfig_bgp/data/integration_tests"
    with open(
        f"{test_path}/{scenario}/openconfig.json",
        encoding="utf-8",
    ) as fd:
        fake_data = json.load(fd)

    with open(
        f"{test_path}/{scenario}/expected_result_{os_name}.txt",
        encoding="utf-8",
    ) as fd:
        expected_result = fd.read()

    return fake_data, expected_result


def mock_get_neighbors(dict_per_address=False):
    """Mock criteo_bgp.get_neighbors."""
    file_path = "tests/states/openconfig_bgp/data"
    if dict_per_address:
        file_path += "/installed_bgp_neighbor_per_address.json"
    else:
        file_path += "/installed_bgp_neighbors.json"

    with open(file_path, encoding="utf-8") as fd:
        return json.load(fd)
