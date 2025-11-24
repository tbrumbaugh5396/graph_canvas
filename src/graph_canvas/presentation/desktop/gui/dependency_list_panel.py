"""
Dependency list sidebar panel shared with the desktop UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple, TYPE_CHECKING

import wx

from graph_canvas.presentation.desktop.models.graph import Graph
from graph_canvas.presentation.desktop.models.node import Node
from graph_canvas.presentation.desktop.models.edge import Edge

if TYPE_CHECKING:
    from graph_canvas.presentation.desktop.gui.main_window import MainWindow


TASK_STATUS_OPTIONS: Sequence[Tuple[Optional[str], str]] = (
    (None, "No Status"),
    ("started", "Started"),
    ("in_progress", "In Progress"),
    ("blocked", "Blocked"),
    ("complete", "Complete"),
)


@dataclass
class TaskRow:
    node: Node
    order: Optional[int]
    prerequisites: List[Node]
    dependents: List[Node]
    status: str  # "ready" or "blocked"


def setup_dependency_list_panel(
    main_window: "MainWindow",
    sidebar_sizer: wx.BoxSizer,
    pane_changed_handler: Callable[[wx.CommandEvent], None],
) -> None:
    """Create the dependency list collapsible pane inside the sidebar."""

    pane = wx.CollapsiblePane(main_window.sidebar, label="Dependency List")
    pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append(pane)
    if pane_changed_handler is not None:
        pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, pane_changed_handler)
    sidebar_sizer.Add(pane, 0, wx.EXPAND | wx.ALL, 5)

    inner = pane.GetPane()
    wrapper = wx.BoxSizer(wx.VERTICAL)

    header_row = wx.BoxSizer(wx.HORIZONTAL)
    summary = wx.StaticText(inner, label="Dependency status will appear here.")
    summary.SetForegroundColour(wx.Colour(15, 23, 42))
    header_row.Add(summary, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
    add_btn = wx.Button(inner, label="Add Task", size=(100, 28))
    add_btn.Bind(wx.EVT_BUTTON, lambda evt: _on_add_task(main_window))
    header_row.Add(add_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
    wrapper.Add(header_row, 0, wx.EXPAND)

    badge_row = wx.BoxSizer(wx.HORIZONTAL)
    ready_label = wx.StaticText(inner, label="Ready: 0")
    ready_label.SetForegroundColour(wx.Colour(15, 23, 42))
    badge_row.Add(ready_label, 0, wx.ALL, 2)
    blocked_label = wx.StaticText(inner, label="Blocked: 0")
    blocked_label.SetForegroundColour(wx.Colour(185, 28, 28))
    badge_row.Add(blocked_label, 0, wx.ALL, 2)
    wrapper.Add(badge_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

    container = wx.Panel(inner)
    container.SetBackgroundColour(wx.Colour(248, 250, 252))
    list_sizer = wx.BoxSizer(wx.VERTICAL)
    container.SetSizer(list_sizer)
    wrapper.Add(container, 1, wx.EXPAND | wx.ALL, 2)

    inner.SetSizer(wrapper)

    # Store references on the main window for later updates
    main_window.dependency_list_pane = pane
    main_window.dependency_summary_label = summary
    main_window.dependency_ready_label = ready_label
    main_window.dependency_blocked_label = blocked_label
    main_window.dependency_list_container = container
    main_window.dependency_list_sizer = list_sizer

    rebuild_dependency_list(main_window)


def rebuild_dependency_list(main_window: "MainWindow") -> None:
    """Update the dependency list from the current graph."""

    container: Optional[wx.Panel] = getattr(main_window, "dependency_list_container", None)
    sizer: Optional[wx.BoxSizer] = getattr(main_window, "dependency_list_sizer", None)
    summary_label: Optional[wx.StaticText] = getattr(
        main_window, "dependency_summary_label", None
    )
    ready_label: Optional[wx.StaticText] = getattr(
        main_window, "dependency_ready_label", None
    )
    blocked_label: Optional[wx.StaticText] = getattr(
        main_window, "dependency_blocked_label", None
    )

    if not container or not sizer or not summary_label or not ready_label or not blocked_label:
        return

    graph: Optional[Graph] = getattr(main_window, "current_graph", None)

    container.Freeze()
    for child in list(container.GetChildren()):
        child.Destroy()

    if not graph or not graph.get_all_nodes():
        summary_label.SetLabel("Add nodes to view the dependency list.")
        ready_label.SetLabel("Ready: 0")
        blocked_label.SetLabel("Blocked: 0")
        placeholder = wx.StaticText(container, label="No tasks available yet.")
        placeholder.SetForegroundColour(wx.Colour(100, 116, 139))
        sizer.Add(placeholder, 0, wx.ALL, 8)
        container.Thaw()
        container.Layout()
        container.GetParent().Layout()
        return

    tasks = derive_task_rows(graph)
    dependency_count = len(graph.get_all_edges())
    summary_label.SetLabel(
        f"Ordered automatically from {dependency_count} "
        f"{'dependency' if dependency_count == 1 else 'dependencies'}."
    )
    ready_label.SetLabel(f"Ready: {sum(1 for task in tasks if task.status == 'ready')}")
    blocked_status_count = sum(1 for task in tasks if read_task_status(task.node) == "blocked")
    blocked_label.SetLabel(f"Blocked: {blocked_status_count}")

    for task in tasks:
        _add_task_row(main_window, container, sizer, task)

    container.Thaw()
    container.Layout()
    container.GetParent().Layout()


def _add_task_row(
    main_window: "MainWindow",
    container: wx.Panel,
    sizer: wx.BoxSizer,
    task: TaskRow,
) -> None:
    panel = wx.Panel(container)
    panel.SetBackgroundColour(wx.Colour(241, 245, 249))
    row_sizer = wx.BoxSizer(wx.VERTICAL)
    panel.SetSizer(row_sizer)

    header = wx.BoxSizer(wx.HORIZONTAL)
    order_label = wx.StaticText(panel, label=str(task.order) if task.order else "—")
    order_label.SetForegroundColour(wx.Colour(15, 23, 42))
    order_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    header.Add(order_label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 6)

    title = wx.StaticText(panel, label=format_node_label(task.node))
    title.SetForegroundColour(wx.Colour(15, 23, 42))
    title.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    header.Add(title, 1, wx.ALIGN_CENTER_VERTICAL)

    topo_status = None
    if task.status == "blocked":
        topo_status = wx.StaticText(panel, label="Resolve cycle")
        topo_status.SetForegroundColour(wx.Colour(185, 28, 28))
        topo_status.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        )
        header.Add(topo_status, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)

    row_sizer.Add(header, 0, wx.EXPAND | wx.BOTTOM, 2)

    prereq_text = (
        "No prerequisites"
        if not task.prerequisites
        else "Depends on " + ", ".join(format_node_label(node) for node in task.prerequisites)
    )
    prereq_label = wx.StaticText(panel, label=prereq_text)
    prereq_label.SetForegroundColour(wx.Colour(71, 85, 105))
    row_sizer.Add(prereq_label, 0, wx.BOTTOM, 2)

    dependents_summary = (
        "Unblocks 0 tasks"
        if not task.dependents
        else f"Unblocks {len(task.dependents)} task{'s' if len(task.dependents) != 1 else ''}"
    )
    if task.dependents:
        dependents_summary += f" • Next: {format_node_label(task.dependents[0])}"
        if len(task.dependents) > 1:
            dependents_summary += " +"
    dependents_label = wx.StaticText(panel, label=dependents_summary)
    dependents_label.SetForegroundColour(wx.Colour(71, 85, 105))
    row_sizer.Add(dependents_label, 0, wx.BOTTOM, 4)

    controls = wx.BoxSizer(wx.HORIZONTAL)
    status_choice = wx.Choice(panel, choices=[label for _, label in TASK_STATUS_OPTIONS])
    status_value = read_task_status(task.node)
    selection_index = 0
    for idx, (value, _) in enumerate(TASK_STATUS_OPTIONS):
        if value == status_value:
            selection_index = idx
            break
    status_choice.SetSelection(selection_index)
    status_choice.Bind(
        wx.EVT_CHOICE,
        lambda event, node_id=task.node.id: _on_status_change(main_window, node_id, event),
    )
    controls.Add(status_choice, 0, wx.RIGHT, 6)

    edit_btn = wx.Button(panel, label="Edit", size=(70, 26))
    edit_btn.Bind(
        wx.EVT_BUTTON,
        lambda event, node_id=task.node.id: _on_edit_task(main_window, node_id),
    )
    controls.Add(edit_btn, 0, wx.RIGHT, 6)

    delete_btn = wx.Button(panel, label="Delete", size=(80, 26))
    delete_btn.SetForegroundColour(wx.Colour(185, 28, 28))
    delete_btn.Bind(
        wx.EVT_BUTTON,
        lambda event, node_id=task.node.id: _on_delete_task(main_window, node_id),
    )
    controls.Add(delete_btn, 0)

    row_sizer.Add(controls, 0, wx.BOTTOM, 4)
    sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 4)


def _on_status_change(main_window: "MainWindow", node_id: str, event: wx.CommandEvent) -> None:
    selection = event.GetSelection()
    status_value = TASK_STATUS_OPTIONS[selection][0]
    main_window.dependency_list_set_status(node_id, status_value)


def _on_delete_task(main_window: "MainWindow", node_id: str) -> None:
    dlg = wx.MessageDialog(
        main_window,
        "Delete this task from the graph?",
        "Delete Task",
        style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
    )
    should_delete = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    if should_delete:
        main_window.dependency_list_delete_node(node_id)


def _on_add_task(main_window: "MainWindow") -> None:
    dialog = DependencyTaskDialog(main_window, main_window.current_graph, None)
    result = dialog.ShowModal()
    data = dialog.get_result() if result == wx.ID_OK else None
    dialog.Destroy()
    if data:
        label, prerequisites, postrequisites = data
        main_window.dependency_list_create_task(label, prerequisites, postrequisites)


def _on_edit_task(main_window: "MainWindow", node_id: str) -> None:
    node = main_window.current_graph.get_node(node_id)
    if not node:
        return
    dialog = DependencyTaskDialog(main_window, main_window.current_graph, node)
    result = dialog.ShowModal()
    data = dialog.get_result() if result == wx.ID_OK else None
    dialog.Destroy()
    if data:
        label, prerequisites, postrequisites = data
        main_window.dependency_list_edit_task(node_id, label, prerequisites, postrequisites)


def derive_task_rows(graph: Optional[Graph]) -> List[TaskRow]:
    if not graph:
        return []

    nodes = graph.get_all_nodes()
    edges = graph.get_all_edges()
    node_map = {node.id: node for node in nodes}

    prerequisites = {node.id: set() for node in nodes}
    dependents = {node.id: set() for node in nodes}

    for edge in edges:
        sources = _gather_members(edge, "source")
        targets = _gather_members(edge, "target")
        for source_id in sources:
            for target_id in targets:
                if source_id == target_id:
                    continue
                prerequisites[target_id].add(source_id)
                dependents[source_id].add(target_id)

    original_prereqs = {node_id: sorted(ids) for node_id, ids in prerequisites.items()}
    original_dependents = {node_id: sorted(ids) for node_id, ids in dependents.items()}

    ready: List[str] = sorted(
        [node_id for node_id, reqs in prerequisites.items() if not reqs],
        key=lambda node_id: _node_sort_key(node_map.get(node_id)),
    )
    visited = set()
    ordered_rows: List[TaskRow] = []

    while ready:
        current_id = ready.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)
        ordered_rows.append(
            TaskRow(
                node=node_map[current_id],
                order=len(ordered_rows) + 1,
                prerequisites=[node_map[node_id] for node_id in original_prereqs[current_id] if node_id in node_map],
                dependents=[node_map[node_id] for node_id in original_dependents[current_id] if node_id in node_map],
                status="ready",
            )
        )
        for dependent_id in list(dependents[current_id]):
            prerequisites[dependent_id].discard(current_id)
            if not prerequisites[dependent_id] and dependent_id not in visited:
                ready.append(dependent_id)
        ready.sort(key=lambda node_id: _node_sort_key(node_map.get(node_id)))

    blocked_rows: List[TaskRow] = []
    for node in nodes:
        if node.id in visited:
            continue
        blocked_rows.append(
            TaskRow(
                node=node,
                order=None,
                prerequisites=[node_map[node_id] for node_id in original_prereqs[node.id] if node_id in node_map],
                dependents=[node_map[node_id] for node_id in original_dependents[node.id] if node_id in node_map],
                status="blocked",
            )
        )
    blocked_rows.sort(key=lambda task: _node_sort_key(task.node))

    return ordered_rows + blocked_rows


def _gather_members(edge: Edge, position: str) -> List[str]:
    ids = set()
    singular = edge.source_id if position == "source" else edge.target_id
    if singular:
        ids.add(singular)
    list_attr = edge.source_ids if position == "source" else edge.target_ids
    if isinstance(list_attr, list):
        ids.update(node_id for node_id in list_attr if isinstance(node_id, str))
    return list(ids)


def _node_sort_key(node: Optional[Node]) -> Tuple[float, float, str]:
    if not node:
        return (float("inf"), float("inf"), "")
    order_meta = read_numeric_metadata(node, "order")
    y_value = node.y if isinstance(node.y, (int, float)) else float("inf")
    text_value = (node.text or "").lower()
    return (
        order_meta if order_meta is not None else float("inf"),
        y_value,
        text_value or node.id,
    )


def read_numeric_metadata(node: Node, key: str) -> Optional[float]:
    metadata = node.metadata or {}
    value = metadata.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def read_task_status(node: Node) -> Optional[str]:
    metadata = node.metadata or {}
    status = metadata.get("status")
    if isinstance(status, str):
        for value, _ in TASK_STATUS_OPTIONS:
            if value == status:
                return status
    return None


def format_node_label(node: Optional[Node]) -> str:
    if not node:
        return "Unknown"
    text = (node.text or "").strip()
    if text:
        return text
    metadata = node.metadata or {}
    for key in ("label", "name"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return node.id


class DependencyTaskDialog(wx.Dialog):
    """Modal dialog for creating or editing dependency list tasks."""

    def __init__(self, parent: wx.Window, graph: Graph, node: Optional[Node] = None):
        title = "Edit Dependency Task" if node else "Add Dependency Task"
        super().__init__(parent, title=title, size=(420, 520))
        self.graph = graph
        self.node = node
        self._result: Optional[Tuple[str, List[str], List[str]]] = None

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        label_text = wx.StaticText(panel, label="Task Label")
        label_text.SetForegroundColour(wx.Colour(15, 23, 42))
        sizer.Add(label_text, 0, wx.ALL, 8)
        self.label_input = wx.TextCtrl(panel, value=node.text if node else "")
        sizer.Add(self.label_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        choices = [
            (candidate.id, format_node_label(candidate))
            for candidate in graph.get_all_nodes()
            if not node or candidate.id != node.id
        ]
        self.choice_ids = [choice[0] for choice in choices]
        display_labels = [choice[1] for choice in choices]

        prereq_label = wx.StaticText(panel, label="Prerequisites (must happen before)")
        prereq_label.SetForegroundColour(wx.Colour(15, 23, 42))
        sizer.Add(prereq_label, 0, wx.ALL, 8)
        self.prereq_list = wx.CheckListBox(panel, choices=display_labels)
        sizer.Add(self.prereq_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        post_label = wx.StaticText(panel, label="Postrequisites (happen after this task)")
        post_label.SetForegroundColour(wx.Colour(15, 23, 42))
        sizer.Add(post_label, 0, wx.ALL, 8)
        self.post_list = wx.CheckListBox(panel, choices=display_labels)
        sizer.Add(self.post_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        if node:
            prereq_ids = {
                edge.source_id
                for edge in graph.get_all_edges()
                if edge.target_id == node.id
            }
            post_ids = {
                edge.target_id
                for edge in graph.get_all_edges()
                if edge.source_id == node.id
            }
            for idx, candidate_id in enumerate(self.choice_ids):
                if candidate_id in prereq_ids:
                    self.prereq_list.Check(idx)
                if candidate_id in post_ids:
                    self.post_list.Check(idx)

        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        if btn_sizer:
            sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        self.Bind(wx.EVT_BUTTON, self._handle_ok, id=wx.ID_OK)

    def _handle_ok(self, event: wx.CommandEvent) -> None:
        label = self.label_input.GetValue().strip()
        if not label:
            wx.MessageBox("Task label is required.", "Validation", wx.ICON_WARNING | wx.OK)
            return

        prereq_ids = [
            self.choice_ids[idx] for idx in self.prereq_list.GetCheckedItems()
        ]
        post_ids = [
            self.choice_ids[idx] for idx in self.post_list.GetCheckedItems()
        ]

        self._result = (label, prereq_ids, post_ids)
        self.EndModal(wx.ID_OK)

    def get_result(self) -> Optional[Tuple[str, List[str], List[str]]]:
        return self._result

