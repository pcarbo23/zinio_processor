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

def test_generate_audio_pool_node():
    from src.core.xml_generator import generate_audio_pool_node, format_duration_hhmmss_mmm
    
    # Test helper first
    assert format_duration_hhmmss_mmm(10000.0) == "00:00:10.000"
    assert format_duration_hhmmss_mmm(90000.0) == "00:01:30.000"
    assert format_duration_hhmmss_mmm(4262061.0) == "01:11:02.061"
    
    audio_data = [
        {"filename": "001.wav", "absolute_path": "/path/to/001.wav", "duration": 10000.0},
        {"filename": "002.wav", "absolute_path": "/path/to/002.wav", "duration": 90000.0}
    ]
    
    node = generate_audio_pool_node(audio_data, "magazine", "/output")
    assert node.tag == "AudioPool"
    assert node.get("Path") == "magazine Files"
    assert node.get("Location") == "/output/magazine Files"
    
    files = list(node)
    assert len(files) == 2
    
    assert files[0].tag == "File"
    assert files[0].get("Id") == "1"
    assert files[0].get("Name") == "001.wav"
    assert files[0].get("OriginalPath") == "/path/to/001.wav"
    assert files[0].get("Duration") == "00:00:10.000"
    
    assert files[1].tag == "File"
    assert files[1].get("Id") == "2"
    assert files[1].get("Name") == "002.wav"
    assert files[1].get("OriginalPath") == "/path/to/002.wav"
    assert files[1].get("Duration") == "00:01:30.000"

def test_generate_tracks_node():
    from src.core.xml_generator import generate_tracks_node
    
    audio_data = [
        {"filename": "001 docTitle Title.wav", "absolute_path": "/path/to/001.wav", "duration": 10000.0},
        {"filename": "002 docAuthor Author Name.wav", "absolute_path": "/path/to/002.wav", "duration": 5000.0},
        {"filename": "004 h1 Section One.wav", "absolute_path": "/path/to/004.wav", "duration": 60000.0}
    ]
    
    node = generate_tracks_node(audio_data)
    assert node.tag == "Tracks"
    
    tracks = list(node)
    assert len(tracks) == 1
    assert tracks[0].tag == "Track"
    assert tracks[0].get("Name") == "Narration"
    
    regions = list(tracks[0])
    assert len(regions) == 3
    
    assert regions[0].tag == "Region"
    assert regions[0].get("Ref") == "1"
    assert regions[0].get("Name") == "001 docTitle Title"
    assert regions[0].get("Start") == "00.000"
    assert regions[0].get("Length") == "10.000"
    
    assert regions[1].tag == "Region"
    assert regions[1].get("Ref") == "2"
    assert regions[1].get("Name") == "002 docAuthor Author Name"
    assert regions[1].get("Start") == "10.000"
    assert regions[1].get("Length") == "05.000"
    
    assert regions[2].tag == "Region"
    assert regions[2].get("Ref") == "3"
    assert regions[2].get("Name") == "004 h1 Section One"
    assert regions[2].get("Start") == "15.000"
    assert regions[2].get("Length") == "01:00.000"



