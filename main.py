from nicegui import ui

from core.ui import main_page

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(main_page, reload= False, native=True,port=8188, title='Traffic Light Optimizer')
