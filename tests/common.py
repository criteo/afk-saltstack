from jinja2 import BaseLoader, Environment


def mock_apply_template_on_contents(contents, template, context, defaults, saltenv):
    """Remove salt:// prefix in path file."""
    context_dict = defaults if defaults else {}
    if context:
        context_dict.update(context)
    # Apply templating
    res = saltTemplates.TEMPLATE_REGISTRY[template](
        contents,
        from_str=True,
        to_str=True,
        context=context_dict,
        saltenv=None,
        grains={},
        pillar={},
        salt={},
        opts={},
    )["data"]
    if isinstance(res, bytes):
        # bytes -> str
        res = res.decode("utf-8")

    return res


def mock_get_file_str(template_name, *_, **__):
    """Remove salt:// prefix in path file."""
    template_name = template_name[7:]
    with open(template_name, encoding="utf-8") as fd:
        content = fd.read()
        return content
