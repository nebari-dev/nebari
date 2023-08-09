from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version


def test_filter_by_highest_supported_k8s_version():
    version_to_filter = "99.99"

    k8s_versions = [
        "1.21.7",
        "1.21.9",
        "1.22.4",
        "1.22.6",
        "1.23.3",
        "1.23.5",
        "1.24.0",
        version_to_filter,
    ]
    actual = filter_by_highest_supported_k8s_version(k8s_versions)
    expected = sorted(list(set(k8s_versions) - {version_to_filter}))
    assert actual == expected
