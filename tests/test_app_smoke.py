import pytest

pytest.importorskip("dash")
pytest.importorskip("plotly")

# pylint: disable=wrong-import-position
from gui.app import create_app


def _ids(component):
    """All component ids present in a Dash layout tree."""
    found = set()
    stack = [component]
    while stack:
        node = stack.pop()
        cid = getattr(node, "id", None)
        if isinstance(cid, str):
            found.add(cid)
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            stack.extend(children)
        elif children is not None:
            stack.append(children)
    return found


def test_app_builds_with_expected_components():
    app = create_app()
    assert app.title == "NETL TRIGA Fuel Loader"
    ids = _ids(app.layout)
    for expected in (
        "core-map",
        "store-groups",
        "store-assignments",
        "input-name",
        "comp-grid",
        "input-sab",
        "btn-add-group",
        "active-group",
        "material-list",
        "btn-generate",
        "btn-save",
        "upload-pattern",
        "download",
        "problem-id",
    ):
        assert expected in ids
