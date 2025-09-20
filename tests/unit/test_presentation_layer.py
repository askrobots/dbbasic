#!/usr/bin/env python3
"""
Tests for the Presentation Layer
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from presentation_layer import PresentationLayer, UIRenderer
from bootstrap_components import ExtendedBootstrapRenderer
from tailwind_components import TailwindRenderer


class TestPresentationLayer:
    """Test the presentation layer core functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        # Register renderers
        PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())
        PresentationLayer.add_renderer('tailwind', TailwindRenderer())

        # Sample data structure
        self.test_data = {
            'type': 'card',
            'title': 'Test Card',
            'description': 'Test Description',
            'body': 'Test Body Content'
        }

    def test_bootstrap_renderer_registered(self):
        """Test Bootstrap renderer is registered"""
        assert 'bootstrap' in PresentationLayer.RENDERERS
        assert isinstance(PresentationLayer.RENDERERS['bootstrap'], ExtendedBootstrapRenderer)

    def test_tailwind_renderer_registered(self):
        """Test Tailwind renderer is registered"""
        assert 'tailwind' in PresentationLayer.RENDERERS
        assert isinstance(PresentationLayer.RENDERERS['tailwind'], TailwindRenderer)

    def test_render_with_bootstrap(self):
        """Test rendering with Bootstrap"""
        html = PresentationLayer.render(self.test_data, 'bootstrap')
        assert html is not None
        assert 'card' in html
        assert 'Test Card' in html
        # When both body and description are provided, body takes precedence
        assert 'Test Body Content' in html

    def test_render_with_tailwind(self):
        """Test rendering with Tailwind"""
        html = PresentationLayer.render(self.test_data, 'tailwind')
        assert html is not None
        assert 'Test Card' in html
        assert 'Test Description' in html

    def test_render_with_invalid_framework(self):
        """Test rendering with invalid framework raises error"""
        with pytest.raises(ValueError, match="Unknown framework"):
            PresentationLayer.render(self.test_data, 'invalid')

    def test_render_string_passthrough(self):
        """Test that strings are passed through unchanged"""
        html = PresentationLayer.render("Hello World", 'bootstrap')
        assert html == "Hello World"

    def test_render_list(self):
        """Test rendering a list of components"""
        data = [
            {'type': 'card', 'title': 'Card 1'},
            {'type': 'card', 'title': 'Card 2'}
        ]
        html = PresentationLayer.render(data, 'bootstrap')
        assert 'Card 1' in html
        assert 'Card 2' in html


class TestBootstrapComponents:
    """Test Bootstrap component rendering"""

    def setup_method(self):
        """Setup test fixtures"""
        self.renderer = ExtendedBootstrapRenderer()

    def test_render_navbar(self):
        """Test navbar rendering"""
        data = {
            'type': 'navbar',
            'brand': 'TestApp',
            'links': [
                {'text': 'Home', 'url': '/'},
                {'text': 'About', 'url': '/about'}
            ]
        }
        html = self.renderer.render(data)
        assert 'navbar' in html
        assert 'TestApp' in html
        assert 'Home' in html
        assert 'About' in html

    def test_render_card(self):
        """Test card rendering"""
        data = {
            'type': 'card',
            'title': 'Test Card',
            'body': 'Card body content'
        }
        html = self.renderer.render(data)
        assert 'card' in html
        assert 'Test Card' in html
        assert 'Card body content' in html

    def test_render_button(self):
        """Test button rendering"""
        data = {
            'type': 'button',
            'text': 'Click Me',
            'variant': 'primary'
        }
        html = self.renderer.render(data)
        assert 'btn' in html
        assert 'btn-primary' in html
        assert 'Click Me' in html

    def test_render_form(self):
        """Test form rendering"""
        data = {
            'type': 'form',
            'fields': [
                {
                    'type': 'input',
                    'name': 'username',
                    'label': 'Username',
                    'placeholder': 'Enter username'
                }
            ]
        }
        html = self.renderer.render(data)
        assert '<form' in html
        assert 'Username' in html
        assert 'Enter username' in html

    def test_render_table(self):
        """Test table rendering"""
        data = {
            'type': 'table',
            'headers': ['Name', 'Age'],
            'rows': [
                ['John', '30'],
                ['Jane', '25']
            ]
        }
        html = self.renderer.render(data)
        assert '<table' in html
        assert 'Name' in html
        assert 'Age' in html
        assert 'John' in html
        assert '30' in html

    def test_render_with_id(self):
        """Test component rendering with ID"""
        data = {
            'type': 'div',
            'id': 'test-div',
            'content': 'Test content'
        }
        html = self.renderer.render(data)
        assert 'id="test-div"' in html
        assert 'Test content' in html


class TestTailwindComponents:
    """Test Tailwind component rendering"""

    def setup_method(self):
        """Setup test fixtures"""
        self.renderer = TailwindRenderer()

    def test_render_card(self):
        """Test Tailwind card rendering"""
        data = {
            'type': 'card',
            'title': 'Tailwind Card',
            'body': 'Card content'
        }
        html = self.renderer.render(data)
        assert 'Tailwind Card' in html
        assert 'Card content' in html
        assert 'shadow' in html  # Tailwind shadow class

    def test_render_button(self):
        """Test Tailwind button rendering"""
        data = {
            'type': 'button',
            'text': 'Tailwind Button',
            'variant': 'primary'
        }
        html = self.renderer.render(data)
        assert 'Tailwind Button' in html
        assert 'bg-indigo' in html  # Tailwind color class

    def test_render_grid(self):
        """Test Tailwind grid rendering"""
        data = {
            'type': 'grid',
            'columns': 3,
            'items': [
                {'type': 'div', 'content': 'Item 1'},
                {'type': 'div', 'content': 'Item 2'},
                {'type': 'div', 'content': 'Item 3'}
            ]
        }
        html = self.renderer.render(data)
        assert 'grid' in html
        assert 'Item 1' in html
        assert 'Item 2' in html
        assert 'Item 3' in html


class TestDataStructureConversion:
    """Test conversion from HTML to data structures"""

    def test_simple_conversion(self):
        """Test that data structures are more efficient than HTML"""
        # HTML approach (old)
        html_string = """
        <div class="card">
            <div class="card-header">
                <h5 class="card-title">User Profile</h5>
            </div>
            <div class="card-body">
                <p class="card-text">User information goes here</p>
            </div>
        </div>
        """

        # Data structure approach (new)
        data_structure = {
            'type': 'card',
            'title': 'User Profile',
            'body': 'User information goes here'
        }

        # Compare sizes (tokens)
        html_tokens = len(html_string.split())
        data_tokens = len(str(data_structure).split())

        # Data structure should be more compact
        assert data_tokens < html_tokens

    def test_framework_agnostic(self):
        """Test same data structure works with multiple frameworks"""
        data = {
            'type': 'alert',
            'message': 'This is a test alert',
            'variant': 'info'
        }

        # Register renderers
        PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())
        PresentationLayer.add_renderer('tailwind', TailwindRenderer())

        # Render with both frameworks
        bootstrap_html = PresentationLayer.render(data, 'bootstrap')
        tailwind_html = PresentationLayer.render(data, 'tailwind')

        # Both should contain the message
        assert 'This is a test alert' in bootstrap_html
        assert 'This is a test alert' in tailwind_html

        # But use different classes
        assert 'alert' in bootstrap_html  # Bootstrap class
        assert 'border-l-4' in tailwind_html  # Tailwind class


class TestComponentMarketplace:
    """Test component marketplace functionality"""

    def test_marketplace_import(self):
        """Test that marketplace can be imported"""
        from component_marketplace import marketplace
        assert marketplace is not None

    def test_get_component(self):
        """Test getting a component from marketplace"""
        from component_marketplace import marketplace
        nav_component = marketplace.get_component('unified-nav')
        assert nav_component is not None
        assert nav_component['name'] == 'Unified Navigation'

    def test_use_component_with_params(self):
        """Test using a component with parameters"""
        from component_marketplace import marketplace
        hero = marketplace.use_component(
            'gradient-hero',
            title='Test Title',
            subtitle='Test Subtitle'
        )
        assert hero['title'] == 'Test Title'
        assert hero['subtitle'] == 'Test Subtitle'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])