"""
Property panel for graph constraints and requirements.
"""

import wx
import wx.adv

from typing import Optional, List, Dict, Any, Callable

import graph_canvas.presentation.desktop.models.graph_restrictions as m_graph_restrictions
import graph_canvas.presentation.desktop.models.graph_property_expression as m_graph_property_expression
import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.event_handlers.property_panel_event_handler as m_property_panel_event_handler


class PropertyExpressionDialog(wx.Dialog):
    """Dialog for creating/editing property expressions."""
    
    def __init__(self, parent, expression: Optional[m_graph_property_expression.PropertyExpression] = None):
        super().__init__(parent, title="Edit Property Expression", size=(500, 400))
        self.expression = expression
        self.setup_ui()
        if expression:
            self.load_expression(expression)
    
    def setup_ui(self):
        """Setup the dialog UI."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Expression type choice
        type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        type_label = wx.StaticText(panel, label="Type:")
        self.type_choice = wx.Choice(panel, choices=["Term", "NOT", "AND", "OR", "IMPLIES"])
        type_sizer.Add(type_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        type_sizer.Add(self.type_choice, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(type_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Term panel
        self.term_panel = wx.Panel(panel)
        term_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Term type choice
        term_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        term_type_label = wx.StaticText(self.term_panel, label="Term Type:")
        self.term_type_choice = wx.Choice(self.term_panel, choices=["Restriction", "Requirement"])
        term_type_sizer.Add(term_type_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        term_type_sizer.Add(self.term_type_choice, 1, wx.EXPAND | wx.ALL, 5)
        term_sizer.Add(term_type_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Value choice
        value_sizer = wx.BoxSizer(wx.HORIZONTAL)
        value_label = wx.StaticText(self.term_panel, label="Value:")
        self.value_choice = wx.Choice(self.term_panel, choices=[])
        value_sizer.Add(value_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        value_sizer.Add(self.value_choice, 1, wx.EXPAND | wx.ALL, 5)
        term_sizer.Add(value_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.term_panel.SetSizer(term_sizer)
        sizer.Add(self.term_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Operator panel
        self.operator_panel = wx.Panel(panel)
        operator_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Sub-expressions list
        self.subexpr_list = wx.ListCtrl(self.operator_panel, style=wx.LC_REPORT)
        self.subexpr_list.InsertColumn(0, "Sub-expressions")
        operator_sizer.Add(self.subexpr_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Add/Remove buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_button = wx.Button(self.operator_panel, label="Add")
        remove_button = wx.Button(self.operator_panel, label="Remove")
        button_sizer.Add(add_button, 0, wx.ALL, 5)
        button_sizer.Add(remove_button, 0, wx.ALL, 5)
        operator_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.operator_panel.SetSizer(operator_sizer)
        sizer.Add(self.operator_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # OK/Cancel buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Bind events
        self.type_choice.Bind(wx.EVT_CHOICE, self.on_type_changed)
        self.term_type_choice.Bind(wx.EVT_CHOICE, self.on_term_type_changed)
        add_button.Bind(wx.EVT_BUTTON, self.on_add_subexpr)
        remove_button.Bind(wx.EVT_BUTTON, self.on_remove_subexpr)
        
        # Initialize UI state
        self.type_choice.SetSelection(0)
        self.term_type_choice.SetSelection(0)
        self.update_value_choices()
        self.update_panels()

    
    def update_value_choices(self):
        """Update value choices based on term type."""
        is_restriction = self.term_type_choice.GetSelection() == 0
        values = (list(m_graph_restrictions.GraphRestriction) if is_restriction 
                 else list(m_graph_restrictions.GraphRequirement))
        self.value_choice.Clear()
        self.value_choice.AppendItems([value.name for value in values])
        if self.value_choice.GetCount() > 0:
            self.value_choice.SetSelection(0)
    
    def update_panels(self):
        """Show/hide panels based on expression type."""
        expr_type = self.type_choice.GetSelection()
        is_term = expr_type == 0
        self.term_panel.Show(is_term)
        self.operator_panel.Show(not is_term)
        self.Layout()
    
    def on_type_changed(self, event):
        """Handle expression type change."""
        self.update_panels()
    
    def on_term_type_changed(self, event):
        """Handle term type change."""
        self.update_value_choices()
    
    def on_add_subexpr(self, event):
        """Add a sub-expression."""
        dialog = PropertyExpressionDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            expr = dialog.get_expression()
            if expr:
                self.subexpr_list.Append([str(expr)])
    
    def on_remove_subexpr(self, event):
        """Remove selected sub-expression."""
        selected = self.subexpr_list.GetFirstSelected()
        if selected >= 0:
            self.subexpr_list.DeleteItem(selected)
    
    def get_expression(self) -> Optional[m_graph_property_expression.PropertyExpression]:
        """Get the created/edited expression."""
        expr_type = self.type_choice.GetSelection()
        if expr_type == 0:  # Term
            is_restriction = self.term_type_choice.GetSelection() == 0
            value_idx = self.value_choice.GetSelection()
            if value_idx < 0:
                return None
            
            value = (list(m_graph_restrictions.GraphRestriction)[value_idx] if is_restriction
                    else list(m_graph_restrictions.GraphRequirement)[value_idx])
            term = m_graph_property_expression.PropertyTerm(is_restriction=is_restriction, value=value)
            return m_graph_property_expression.PropertyExpression.create_term(term)
        
        # Operator expression
        terms = []
        for i in range(self.subexpr_list.GetItemCount()):
            expr = self.subexpr_list.GetItem(i).GetData()
            if expr:
                terms.append(expr)
        
        if expr_type == 1:  # NOT
            if terms:
                return m_graph_property_expression.PropertyExpression.create_not(terms[0])
        elif expr_type == 2:  # AND
            if terms:
                return m_graph_property_expression.PropertyExpression.create_and(terms)
        elif expr_type == 3:  # OR
            if terms:
                return m_graph_property_expression.PropertyExpression.create_or(terms)
        elif expr_type == 4:  # IMPLIES
            if len(terms) >= 2:
                return m_graph_property_expression.PropertyExpression.create_implies(terms[0], terms[1])
        
        return None
    
    def load_expression(self, expression: m_graph_property_expression.PropertyExpression):
        """Load an existing expression for editing."""
        if expression.term is not None:  # Term
            self.type_choice.SetSelection(0)
            self.term_type_choice.SetSelection(0 if expression.term.is_restriction else 1)
            self.update_value_choices()
            value_list = (list(m_graph_restrictions.GraphRestriction) if expression.term.is_restriction
                         else list(m_graph_restrictions.GraphRequirement))
            try:
                value_idx = value_list.index(expression.term.value)
                self.value_choice.SetSelection(value_idx)
            except ValueError:
                pass
        else:  # Operator
            if expression.operator == m_graph_property_expression.LogicalOperator.NOT:
                self.type_choice.SetSelection(1)
            elif expression.operator == m_graph_property_expression.LogicalOperator.AND:
                self.type_choice.SetSelection(2)
            elif expression.operator == m_graph_property_expression.LogicalOperator.OR:
                self.type_choice.SetSelection(3)
            
            for term in expression.terms:
                self.subexpr_list.Append([str(term)])
                self.subexpr_list.SetItemData(self.subexpr_list.GetItemCount() - 1, term)
        
        self.update_panels()


class PropertyPanel(wx.Panel):
    """Panel for managing graph properties and constraints."""
    
    def __init__(self, parent: wx.Window):
        super().__init__(parent)
        # Find main window by walking up the parent chain
        window = parent
        while window and not isinstance(window, wx.Frame):
            window = window.GetParent()
        self.main_window = window
        self.expressions: List[m_graph_property_expression.PropertyExpression] = []
        self.setup_ui()
        self.start_validation_timer()
    
    def setup_ui(self):
        """Setup the panel UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(self, label="Graph Properties")
        header.SetFont(wx.Font(wx.FontInfo(12).Bold()))
        sizer.Add(header, 0, wx.ALL, 5)
        
        # Property list
        self.property_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.property_list.InsertColumn(0, "Property")
        self.property_list.InsertColumn(1, "Status")
        sizer.Add(self.property_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_button = wx.Button(self, label="Add")
        edit_button = wx.Button(self, label="Edit")
        remove_button = wx.Button(self, label="Remove")
        button_sizer.Add(add_button, 0, wx.ALL, 5)
        button_sizer.Add(edit_button, 0, wx.ALL, 5)
        button_sizer.Add(remove_button, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(sizer)
        
        # Bind events
        add_button.Bind(wx.EVT_BUTTON, self.on_add)
        edit_button.Bind(wx.EVT_BUTTON, self.on_edit)
        remove_button.Bind(wx.EVT_BUTTON, self.on_remove)
        self.property_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.property_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_selection_changed)
    
    def start_validation_timer(self):
        """Start timer for periodic validation."""
        self.validation_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_validation_timer, self.validation_timer)
        self.validation_timer.Start(1000)  # Check every second
    
    def on_validation_timer(self, event):
        """Handle validation timer event."""
        self.validate_all()
    
    def validate_all(self):
        """Validate all expressions and update UI."""
        for i, expr in enumerate(self.expressions):
            is_valid = expr.evaluate(self.main_window.current_graph)
            self.property_list.SetItem(i, 1, "✓" if is_valid else "✗")
            
            if not is_valid:
                errors = expr.get_validation_errors(self.main_window.current_graph)
                if errors:
                    wx.CallAfter(self.show_error_dialog, expr, errors)
    
    def show_error_dialog(self, expr: m_graph_property_expression.PropertyExpression, errors: List[str]):
        """Show error dialog for failed validation."""
        dialog = wx.MessageDialog(
            self,
            f"Property '{expr}' is violated:\n\n" + "\n".join(f"- {error}" for error in errors),
            "Property Violation",
            wx.OK | wx.ICON_WARNING
        )
        dialog.ShowModal()
    
    def on_add(self, event):
        """Handle add button click."""
        dialog = PropertyExpressionDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            expr = dialog.get_expression()
            if expr:
                self.expressions.append(expr)
                idx = self.property_list.GetItemCount()
                self.property_list.InsertItem(idx, str(expr))
                self.property_list.SetItem(idx, 1, "")
                self.validate_all()
    
    def on_edit(self, event):
        """Handle edit button click."""
        selected = self.property_list.GetFirstSelected()
        if selected >= 0:
            dialog = PropertyExpressionDialog(self, self.expressions[selected])
            if dialog.ShowModal() == wx.ID_OK:
                expr = dialog.get_expression()
                if expr:
                    self.expressions[selected] = expr
                    self.property_list.SetItem(selected, 0, str(expr))
                    self.property_list.SetItem(selected, 1, "")
                    self.validate_all()
    
    def on_remove(self, event):
        """Handle remove button click."""
        selected = self.property_list.GetFirstSelected()
        if selected >= 0:
            self.expressions.pop(selected)
            self.property_list.DeleteItem(selected)
    
    def on_selection_changed(self, event):
        """Handle property list selection change."""
        has_selection = self.property_list.GetFirstSelected() >= 0
        for child in self.GetChildren():
            if isinstance(child, wx.Button):
                if child.GetLabel() in ("Edit", "Remove"):
                    child.Enable(has_selection)
    
    def save_properties(self) -> List[Dict[str, Any]]:
        """Save properties to dictionary format."""
        return [expr.to_dict() for expr in self.expressions]
    
    def load_properties(self, data: List[Dict[str, Any]]):
        """Load properties from dictionary format."""
        self.expressions = []
        self.property_list.DeleteAllItems()
        
        for expr_data in data:
            expr = m_graph_property_expression.PropertyExpression.from_dict(expr_data)
            self.expressions.append(expr)
            idx = self.property_list.GetItemCount()
            self.property_list.InsertItem(idx, str(expr))
            self.property_list.SetItem(idx, 1, "")
