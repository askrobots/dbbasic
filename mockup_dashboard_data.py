# Generated from mockup_dashboard.html
from presentation_layer import PresentationLayer

mockup_data = {'type': 'page', 'title': 'DBBasic Dashboard - 402M rows/sec', 'components': [{'type': 'navbar', 'brand': 'DBBasic'}, {'type': 'container', 'children': []}]}

# Render to HTML
html = PresentationLayer.render(mockup_data, 'bootstrap')
