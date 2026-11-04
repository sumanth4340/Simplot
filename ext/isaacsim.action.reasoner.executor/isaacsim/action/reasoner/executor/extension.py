"""Extension entrypoint: menu item + window lifetime."""
from __future__ import annotations

import omni.ext
import omni.kit.actions.core
from omni.kit.menu.utils import (
    MenuItemDescription,
    add_menu_items,
    build_submenu_dict,
)

try:
    from omni.kit.menu.utils import remove_menu_items
except Exception:  # older Kit without removal helper
    remove_menu_items = None

MENU_PATH = "Window/Action Reasoner"


class ActionReasonerExecutorExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self._ext_id = ext_id
        self._name = omni.ext.get_extension_name(ext_id)
        self._window = None
        registry = omni.kit.actions.core.get_action_registry()
        registry.register_action(
            self._name,
            "show_window",
            self.show_window,
            display_name="Show Action Reasoner",
            description="Show the Action Reasoner prompt window",
        )
        menu = build_submenu_dict(
            [MenuItemDescription(name=MENU_PATH, onclick_action=(self._name, "show_window"))]
        )
        for group in menu:
            add_menu_items(menu[group], group)
        self.show_window()

    def on_shutdown(self) -> None:
        if self._window is not None:
            try:
                destroy = getattr(self._window, "destroy", None)
                if destroy is not None:
                    destroy()
            except Exception:
                pass
        try:
            registry = omni.kit.actions.core.get_action_registry()
            registry.deregister_action(self._name, "show_window")
        except Exception:
            pass
        if remove_menu_items is not None:
            try:
                remove_menu_items([MENU_PATH])
            except Exception:
                pass
        self._window = None

    def show_window(self) -> None:
        from .window import ReasonerWindow

        if self._window is None:
            self._window = ReasonerWindow()
        self._window.show()
