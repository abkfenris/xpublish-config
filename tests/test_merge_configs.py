from xpublish_config.merge_configs import merge


def test_merge():
    a = {"first": {"all_rows": {"pass": "dog", "number": "1"}}}
    b = {"first": {"all_rows": {"fail": "cat", "number": "5"}}}

    assert merge(b, a) == {
        "first": {"all_rows": {"pass": "dog", "fail": "cat", "number": "5"}},
    }

    assert b == {"first": {"all_rows": {"fail": "cat", "number": "5"}}}
