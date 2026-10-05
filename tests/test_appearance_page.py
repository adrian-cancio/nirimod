"""Tests for AppearancePage configuration helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock
import pytest

pytest.importorskip("gi")

from nirimod.kdl_parser import KdlNode, find_or_create, parse_kdl, write_kdl
from nirimod.pages.appearance import AppearancePage


class DummyWindow:
    def __init__(self, nodes: list[KdlNode]):
        self._nodes = nodes
        self.app_state = MagicMock()
        self.app_state.write_current_kdl.return_value = write_kdl(nodes)
        self.app_state.saved_kdl = ""
        self.app_state.undo = MagicMock()
        self.app_state.undo.last_snapshot = None

    def get_nodes(self) -> list[KdlNode]:
        return self._nodes

    def push_undo(self, description: str, before: str, after: str):
        pass

    def mark_clean(self):
        pass

    def mark_dirty(self):
        pass

    def show_toast(self, msg: str, timeout: int = 3):
        pass


class TestAppearancePage(unittest.TestCase):
    def setUp(self):
        kdl = """layout {
    gaps 8
    shadow {
        softness 30
        spread 5
    }
}
blur {
    passes 3
    offset 2
}
"""
        self.nodes = parse_kdl(kdl)
        self.win = DummyWindow(self.nodes)
        self.page = AppearancePage(self.win)

    def test_draw_behind_window_toggle(self):
        self.page._set_shadow_flag("draw-behind-window", True)
        shadow = find_or_create(self.nodes, "layout", "shadow")
        dbw = shadow.get_child("draw-behind-window")
        self.assertIsNotNone(dbw)
        self.assertEqual(dbw.args, [True])

        out = write_kdl(self.nodes)
        self.assertIn("draw-behind-window true", out)

        self.page._set_shadow_flag("draw-behind-window", False)
        shadow = find_or_create(self.nodes, "layout", "shadow")
        self.assertIsNone(shadow.get_child("draw-behind-window"))

        out_after = write_kdl(self.nodes)
        self.assertNotIn("draw-behind-window", out_after)

    def test_blur_toggle_isolation(self):
        self.page._set_blur_effects_enabled(False)
        blur = find_or_create(self.nodes, "blur")
        self.assertIsNotNone(blur.get_child("off"))

        self.page._set_blur_effects_enabled(True)
        blur = find_or_create(self.nodes, "blur")
        self.assertIsNone(blur.get_child("off"))

        rules = [n for n in self.nodes if n.name == "window-rule"]
        self.assertEqual(rules, [])

    def test_window_opacity_slider(self):
        self.page._set_window_opacity(0.85)
        out = write_kdl(self.nodes)
        self.assertIn("opacity 0.85", out)

        self.page._set_window_opacity(1.0)
        out_after = write_kdl(self.nodes)
        self.assertNotIn("opacity", out_after)

    def test_draw_behind_window_flag_and_false(self):
        kdl_flag = "layout { shadow { draw-behind-window; } }\n"
        nodes_flag = parse_kdl(kdl_flag)
        shadow_flag = find_or_create(nodes_flag, "layout", "shadow")
        dbw_flag = shadow_flag.get_child("draw-behind-window")
        self.assertTrue(
            dbw_flag is not None and (not dbw_flag.args or dbw_flag.args[0] is True)
        )

        kdl_false = "layout { shadow { draw-behind-window false; } }\n"
        nodes_false = parse_kdl(kdl_false)
        shadow_false = find_or_create(nodes_false, "layout", "shadow")
        dbw_false = shadow_false.get_child("draw-behind-window")
        self.assertFalse(
            dbw_false is not None and (not dbw_false.args or dbw_false.args[0] is True)
        )

    def test_shadow_on_removes_off_child(self):
        kdl_off = "layout { shadow { off; } }\n"
        nodes = parse_kdl(kdl_off)
        page = AppearancePage(DummyWindow(nodes))
        page._set_shadow_flag("on", True)
        shadow = find_or_create(nodes, "layout", "shadow")
        self.assertIsNone(shadow.get_child("off"))
        self.assertIsNotNone(shadow.get_child("on"))
        out = write_kdl(nodes)
        self.assertIn("on", out)
        self.assertNotIn("off", out)


if __name__ == "__main__":
    unittest.main()
