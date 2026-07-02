"""Dash app: define fuel groups (incl. composition), paint them onto the core, and
generate a specs.py.

Run with::

    python -m gui.app

Every fuel location always carries a material: on startup all locations use a
default fuel group; painting overrides individual locations. Fuel-group
definitions include an editable composition grid (nuclide vs element is
inferred from the species format) and S(a,b) laws.
"""

from __future__ import annotations

import dash
import dash_ag_grid as dag
from dash import ALL, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

from gui import state
from gui.hexmap import build_core_figure, selected_location_from_click
from gui.problems import available_problems

_LABEL = {"display": "block", "fontSize": "13px", "marginTop": "6px", "fontWeight": "bold"}
_INPUT = {"width": "100%", "boxSizing": "border-box"}
_SHORT_INPUT = {"width": "40%", "boxSizing": "border-box"}


def _problem_options():
    problems = available_problems()
    return [{"label": pid, "value": pid} for pid in problems], (problems[0] if problems else None)


def _composition_grid() -> dag.AgGrid:
    return dag.AgGrid(
        id="comp-grid",
        columnDefs=[
            {"field": "species", "editable": True, "checkboxSelection": True, "headerCheckboxSelection": True},
            {"field": "fraction", "editable": True, "type": "numericColumn"},
        ],
        rowData=state.default_composition_rows(),
        columnSize="sizeToFit",
        dashGridOptions={"singleClickEdit": True, "rowSelection": "multiple", "animateRows": False},
        style={"height": "240px"},
    )


def _controls() -> html.Div:
    problem_options, problem_value = _problem_options()
    return html.Div(
        style={"width": "380px", "flex": "0 0 380px"},
        children=[
            html.Label("Problem", style=_LABEL),
            dcc.Dropdown(
                id="problem-id", options=problem_options, value=problem_value, clearable=False, style={"width": "40%"}
            ),
            html.Hr(),
            html.H4("Material", style={"margin": "4px 0"}),
            html.Label("Name", style=_LABEL),
            dcc.Input(
                id="input-name",
                type="text",
                value=state.suggested_name([state.default_group()]),
                placeholder="e.g. Fuel Material 2",
                style=_SHORT_INPUT,
            ),
            html.Label("Density (g/cm3)", style=_LABEL),
            dcc.Input(id="input-density", type="number", value=5.85, step="any", style=_SHORT_INPUT),
            html.Label("Temperature (K)", style=_LABEL),
            dcc.Input(id="input-temp", type="number", value=600.0, step="any", style=_SHORT_INPUT),
            html.Label("Fraction type", style=_LABEL),
            dcc.RadioItems(
                id="percent-type",
                options=[{"label": "weight (wo)", "value": "wo"}, {"label": "atom (ao)", "value": "ao"}],
                value="wo",
                inline=True,
                style={"fontSize": "13px"},
            ),
            html.Label("Composition", style=_LABEL),
            _composition_grid(),
            html.Div(
                [
                    html.Button("Add row", id="btn-add-row", n_clicks=0),
                    html.Button("Delete selected", id="btn-del-rows", n_clicks=0, style={"marginLeft": "6px"}),
                ],
                style={"marginTop": "4px"},
            ),
            html.Label("S(a,b) laws (one per line)", style=_LABEL),
            dcc.Textarea(
                id="input-sab",
                value=state.sab_to_text(["c_H_in_ZrH", "c_Zr_in_ZrH"]),
                style={"width": "100%", "height": "56px", "fontFamily": "monospace", "fontSize": "12px"},
            ),
            html.Button("Update Material", id="btn-add-group", n_clicks=0, style={"marginTop": "8px"}),
            html.Div(id="status-edit", style={"fontSize": "12px", "color": "#a00", "minHeight": "16px"}),
            html.Hr(),
            html.Label("Materials", style=_LABEL),
            dcc.Store(id="active-group", data=state.DEFAULT_GROUP_NAME),
            html.Div(id="material-list"),
            html.Hr(),
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "6px"},
                children=[
                    html.Button("Save pattern", id="btn-save", n_clicks=0),
                    dcc.Upload(
                        id="upload-pattern",
                        children=html.Button("Load pattern"),
                        style={"width": "auto", "display": "inline-block"},
                    ),
                ],
            ),
            html.Div(
                html.Button("Generate Input File", id="btn-generate", n_clicks=0),
                style={"marginTop": "8px"},
            ),
            html.Div(id="status-action", style={"fontSize": "12px", "color": "#060", "minHeight": "16px"}),
            dcc.Download(id="download"),
        ],
    )


_MATERIAL_ROW_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "padding": "3px 6px",
    "marginBottom": "2px",
    "cursor": "pointer",
    "fontSize": "13px",
    "border": "1px solid transparent",
    "borderRadius": "3px",
}
_MATERIAL_ROW_ACTIVE_STYLE = {**_MATERIAL_ROW_STYLE, "border": "1px solid #333", "backgroundColor": "#eef"}


def _swatch(color: str) -> html.Span:
    return html.Span(
        style={
            "display": "inline-block",
            "width": "12px",
            "height": "12px",
            "backgroundColor": color,
            "border": "1px solid #333",
            "flex": "0 0 auto",
        }
    )


def _material_row_style(name, active):
    return _MATERIAL_ROW_ACTIVE_STYLE if name == active else _MATERIAL_ROW_STYLE


def _material_list_children(names, group_colors, active):
    """Clickable rows (name + color swatch) for selecting the active material."""
    rows = []
    for name in sorted(names):
        rows.append(
            html.Div(
                [html.Span(name), _swatch(group_colors[name])],
                id={"type": "material-option", "index": name},
                n_clicks=0,
                style=_material_row_style(name, active),
            )
        )
    return rows


def create_app() -> dash.Dash:
    """Build the Dash application."""
    dash_app = dash.Dash(__name__)
    dash_app.title = "NETL TRIGA Fuel Loader"

    dash_app.layout = html.Div(
        style={"maxWidth": "1250px", "margin": "0 auto", "fontFamily": "sans-serif"},
        children=[
            html.H2("NETL TRIGA Fuel Loader"),
            html.Div(
                style={"display": "flex", "gap": "16px", "alignItems": "flex-start"},
                children=[
                    _controls(),
                    dcc.Graph(
                        id="core-map", figure=build_core_figure(), config={"displayModeBar": False}, style={"flex": "1 1 auto"}
                    ),
                ],
            ),
            dcc.Store(id="store-groups", data=[state.default_group()]),
            dcc.Store(id="store-assignments", data=state.initial_assignments()),
        ],
    )

    @dash_app.callback(
        Output("store-groups", "data"),
        Output("store-assignments", "data"),
        Output("status-edit", "children"),
        Output("active-group", "data", allow_duplicate=True),
        Input("btn-add-group", "n_clicks"),
        Input("core-map", "clickData"),
        Input("upload-pattern", "contents"),
        State("input-name", "value"),
        State("input-density", "value"),
        State("input-temp", "value"),
        State("percent-type", "value"),
        State("input-sab", "value"),
        State("comp-grid", "virtualRowData"),
        State("comp-grid", "rowData"),
        State("active-group", "data"),
        State("store-groups", "data"),
        State("store-assignments", "data"),
        prevent_initial_call=True,
    )
    def _update_state(
        _add,
        click_data,
        upload_contents,
        name,
        density,
        temp,
        percent_type,
        sab,
        virtual_rows,
        row_data,
        active,
        groups,
        assignments,
    ):
        groups = groups or []
        assignments = assignments or {}
        trigger = ctx.triggered_id
        try:
            if trigger == "btn-add-group":
                nuclides, elements = state.composition_from_rows(virtual_rows or row_data)
                updated = state.upsert_group(
                    groups,
                    name,
                    density,
                    temp,
                    nuclides=nuclides,
                    elements=elements,
                    percent_type=percent_type,
                    s_alpha_beta=state.sab_from_text(sab),
                )
                return updated, no_update, "", (name or "").strip()
            if trigger == "core-map":
                location = selected_location_from_click(click_data)
                if not location:
                    raise PreventUpdate
                return no_update, state.paint(assignments, location, active), "", no_update
            if trigger == "upload-pattern":
                if not upload_contents:
                    raise PreventUpdate
                new_groups, new_assignments = state.load_pattern(upload_contents)
                return new_groups, new_assignments, "", state.most_common_group(new_assignments)
        except PreventUpdate:
            raise
        except (ValueError, KeyError, TypeError) as error:
            return no_update, no_update, f"Error: {error}", no_update
        raise PreventUpdate

    @dash_app.callback(
        Output("core-map", "figure"),
        Input("store-groups", "data"),
        Input("store-assignments", "data"),
    )
    def _render_core_map(groups, assignments):
        groups = groups or []
        assignments = assignments or {}
        colors = state.group_color_map(group["name"] for group in groups)
        return build_core_figure(assignments=assignments, group_colors=colors)

    @dash_app.callback(
        Output("material-list", "children"),
        Input("store-groups", "data"),
        State("active-group", "data"),
    )
    def _render_material_list(groups, active):
        # Regenerated only when the set of materials changes (not on every paint),
        # since recreating these rows resets their n_clicks and would otherwise
        # spuriously re-trigger _select_material below.
        groups = groups or []
        names = [group["name"] for group in groups]
        colors = state.group_color_map(names)
        return _material_list_children(names, colors, active)

    @dash_app.callback(
        Output({"type": "material-option", "index": ALL}, "style"),
        Input("active-group", "data"),
        State({"type": "material-option", "index": ALL}, "id"),
    )
    def _highlight_active_material(active, ids):
        # Re-styles the existing rows in place (no children/n_clicks touched) so
        # selecting a material never resets another row's click-tracking state.
        return [_material_row_style(component_id["index"], active) for component_id in (ids or [])]

    @dash_app.callback(
        Output("active-group", "data", allow_duplicate=True),
        Input({"type": "material-option", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_material(_n_clicks):
        triggered = ctx.triggered
        if not triggered or not triggered[0]["value"]:
            # No real trigger, or n_clicks reset to 0/None by a redraw -- not a click.
            raise PreventUpdate
        return ctx.triggered_id["index"]

    @dash_app.callback(
        Output("input-name", "value"),
        Output("input-density", "value"),
        Output("input-temp", "value"),
        Output("percent-type", "value"),
        Output("input-sab", "value"),
        Input("active-group", "data"),
        State("store-groups", "data"),
        prevent_initial_call=True,
    )
    def _load_group_into_form(active, groups):
        group = next((g for g in (groups or []) if g["name"] == active), None)
        if group is None:
            raise PreventUpdate
        return (
            group["name"],
            group["density"],
            group["temperature"],
            group["percent_type"],
            state.sab_to_text(group["s_alpha_beta"]),
        )

    @dash_app.callback(
        Output("comp-grid", "rowData"),
        Input("active-group", "data"),
        Input("btn-add-row", "n_clicks"),
        Input("btn-del-rows", "n_clicks"),
        State("comp-grid", "virtualRowData"),
        State("comp-grid", "selectedRows"),
        State("store-groups", "data"),
        prevent_initial_call=True,
    )
    def _grid(active, _add_row, _del_rows, current_rows, selected_rows, groups):
        trigger = ctx.triggered_id
        current_rows = current_rows or []
        if trigger == "btn-add-row":
            return current_rows + [{"species": "", "fraction": 0.0}]
        if trigger == "btn-del-rows":
            selected = selected_rows or []
            return [row for row in current_rows if row not in selected]
        group = next((g for g in (groups or []) if g["name"] == active), None)
        if group is None:
            raise PreventUpdate
        return state.rows_from_spec(group)

    @dash_app.callback(
        Output("download", "data"),
        Output("status-action", "children"),
        Input("btn-generate", "n_clicks"),
        Input("btn-save", "n_clicks"),
        State("store-groups", "data"),
        State("store-assignments", "data"),
        State("problem-id", "value"),
        prevent_initial_call=True,
    )
    def _download(_gen, _save, groups, assignments, problem_id):
        groups = groups or []
        assignments = assignments or {}
        try:
            if ctx.triggered_id == "btn-generate":
                text = state.generate_specs_text(groups, assignments, problem_id or "")
                return dcc.send_string(text, f"{problem_id}_specs.py"), "Generated specs.py"
            return dcc.send_string(state.pattern_json(groups, assignments), "loading_pattern.json"), "Saved pattern"
        except (ValueError, KeyError, TypeError) as error:
            return no_update, f"Error: {error}"

    return dash_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
