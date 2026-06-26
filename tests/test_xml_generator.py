import os
import tempfile
from src.core.xml_generator import write_boilerplate_css, DAISY_BOILERPLATE_CSS

def test_write_boilerplate_css():
    with tempfile.TemporaryDirectory() as tmpdir:
        css_path = write_boilerplate_css(tmpdir)
        assert os.path.exists(css_path)
        assert os.path.basename(css_path) == "style.css"
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == DAISY_BOILERPLATE_CSS

def test_get_static_text_items():
    from src.core.xml_generator import get_static_text_items
    element = get_static_text_items()
    assert element is not None
    assert element.tag == "TextItems"
    
    # Check that it contains TextItem children (there should be 17 child nodes)
    children = list(element)
    assert len(children) == 17
    assert all(child.tag == "TextItem" for child in children)
    
    # Check a specific child, e.g. first child Name="Title"
    assert children[0].get("Name") == "Title"
    assert children[0].get("State") == "1"
    assert children[0].get("Key") == "1"
    
    # Check that it contains structured inner tag
    h1_child = children[0].find("h1")
    assert h1_child is not None
    assert h1_child.get("class") == "docTitle"
    assert h1_child.text == "Title"

