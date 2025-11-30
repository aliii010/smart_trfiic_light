from nicegui import ui


def header():
    with ui.header().style(
            'background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: 100%; height: 64px;'):
        with ui.row().classes('items-center q-gutter-md'):
            ui.label('Smart Traffic light flow optimization').classes('text-primary text-h5 text-weight-bold')