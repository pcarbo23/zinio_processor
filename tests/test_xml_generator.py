import os
import tempfile
import xml.etree.ElementTree as ET
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
    assert files[0].get("Duration") == "10.000"
    
    assert files[1].tag == "File"
    assert files[1].get("Id") == "2"
    assert files[1].get("Name") == "002.wav"
    assert files[1].get("OriginalPath") == "/path/to/002.wav"
    assert files[1].get("Duration") == "01:30.000"

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

def test_generate_document_xhtml():
    from src.core.xml_generator import generate_document_xhtml
    import xml.etree.ElementTree as ET
    
    metadata = {
        "title": "Mock Magazine",
        "creator": "Author Name",
        "identifier": "us-nls-mock2026",
        "publisher": "National Library Service",
        "generator": "Hindenburg ABC"
    }
    
    audio_data = [
        {"filename": "001 docTitle Title.wav"},
        {"filename": "002 docAuthor Author Name.wav"},
        {"filename": "003 World News – Europe.wav"},
        {"filename": "004 World News – Asia.wav"},
        {"filename": "005 Standalone Article.wav"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        xhtml_path = generate_document_xhtml(audio_data, metadata, tmpdir)
        assert os.path.exists(xhtml_path)
        assert os.path.basename(xhtml_path) == "Document.xhtml"
        
        # Verify the XML declaration format uses double quotes
        with open(xhtml_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        assert first_line == '<?xml version="1.0" encoding="UTF-8"?>'
        
        # Parse output file to verify tags
        tree = ET.parse(xhtml_path)
        root = tree.getroot()
        
        # Verify namespace and root tag
        assert "html" in root.tag
        
        # Verify head meta tags
        title = root.find(".//{http://www.w3.org/1999/xhtml}title")
        assert title is not None
        assert title.text == "Mock Magazine"
        
        meta_creator = root.find(".//{http://www.w3.org/1999/xhtml}meta[@name='dc:creator']")
        assert meta_creator is not None
        assert meta_creator.get("content") == "Author Name"
        
        # Verify body elements
        body = root.find(".//{http://www.w3.org/1999/xhtml}body")
        assert body is not None
        
        # Convert children tags/text/ids to list for easy verification
        elements = []
        for child in body:
            # strip namespace from tag
            tag_name = child.tag.split("}")[-1]
            elements.append({
                "tag": tag_name,
                "id": child.get("id"),
                "class": child.get("class"),
                "text": child.text
            })
            
        # Expected sequence:
        # 1. <h1> class="docTitle" -> "Title"
        # 2. <h1> class="docAuthor" -> "Author Name"
        # 3. <h1> -> "World News"
        # 4. <h2> class="article" -> "Europe"
        # 5. <h2> class="article" -> "Asia" (no new section generated because it's the same)
        # 6. <h1> class="article" -> "Standalone Article"
        
        assert len(elements) == 6
        
        assert elements[0] == {"tag": "h1", "id": "hix00001", "class": "docTitle", "text": "Title"}
        assert elements[1] == {"tag": "h1", "id": "hix00002", "class": "docAuthor", "text": "Author Name"}
        assert elements[2] == {"tag": "h1", "id": "hix00003", "class": None, "text": "World News"}
        assert elements[3] == {"tag": "h2", "id": "hix00004", "class": "article", "text": "Europe"}
        assert elements[4] == {"tag": "h2", "id": "hix00005", "class": "article", "text": "Asia"}
        assert elements[5] == {"tag": "h1", "id": "hix00006", "class": "article", "text": "Standalone Article"}

def test_generate_nav_points_node():
    from src.core.xml_generator import generate_nav_points_node
    
    audio_data = [
        {"filename": "001 docTitle Title.wav", "duration": 10000.0},
        {"filename": "002 docAuthor Author Name.wav", "duration": 5000.0},
        {"filename": "003 World News – Europe.wav", "duration": 30000.0}
    ]
    
    node = generate_nav_points_node(audio_data)
    assert node.tag == "NavPoints"
    
    navs = list(node)
    # 4 headings generated: Title, Author, World News (section), Europe (article).
    # 2 navpoints each = 8 total navpoints.
    assert len(navs) == 8
    
    # Assert they are grouped consecutively
    # Title (hix00001) starts at 0.0s (00.000)
    assert navs[0].get("Id") == "hix00001"
    assert navs[0].get("Begin") == "00.000"
    assert navs[1].get("Id") == "hix00001"
    assert navs[1].get("Begin") == "03.000"
    
    # Author (hix00002) starts at 10.0s (10.000)
    assert navs[2].get("Id") == "hix00002"
    assert navs[2].get("Begin") == "10.000"
    assert navs[3].get("Id") == "hix00002"
    assert navs[3].get("Begin") == "13.000"
    
    # World News (hix00003) starts at 15.0s (15.000)
    assert navs[4].get("Id") == "hix00003"
    assert navs[4].get("Begin") == "15.000"
    assert navs[5].get("Id") == "hix00003"
    assert navs[5].get("Begin") == "18.000"
    
    # Europe (hix00004) starts at 15.0s (15.000)
    assert navs[6].get("Id") == "hix00004"
    assert navs[6].get("Begin") == "15.000"
    assert navs[7].get("Id") == "hix00004"
    assert navs[7].get("Begin") == "18.000"

def test_compile_hindenburg_session():
    from src.core.xml_generator import compile_hindenburg_session
    
    metadata = {
        "copyright": "Restricted",
        "title": "Compiled Magazine",
        "producer": "Producer unit test",
        "recording_agency": "Agency unit test"
    }
    
    audio_data = [
        {"filename": "001 docTitle Title.wav", "absolute_path": "/path/001.wav", "duration": 10000.0},
        {"filename": "002 docAuthor Author Name.wav", "absolute_path": "/path/002.wav", "duration": 5000.0}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        nhsx_path = compile_hindenburg_session(audio_data, metadata, tmpdir, "mag_proj")
        assert os.path.exists(nhsx_path)
        assert os.path.basename(nhsx_path) == "mag_proj.nhsx"
        
        # Verify the XML declaration format uses double quotes
        with open(nhsx_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        assert first_line == '<?xml version="1.0" encoding="UTF-8"?>'
        
        # Verify XML structure compiles and contains correct elements
        tree = ET.parse(nhsx_path)
        root = tree.getroot()
        assert root.tag == "Session"
        assert root.get("Version") == "Narrator Studio 1.60"
        
        info = root.find("Info")
        assert info is not None
        assert info.get("Title") == "Compiled Magazine"
        assert info.get("Producer") == "Producer unit test"
        
        audio_pool = root.find("AudioPool")
        assert audio_pool is not None
        assert len(list(audio_pool)) == 2
        
        tracks = root.find("Tracks")
        assert tracks is not None
        
        navs = root.find("NavPoints")
        assert navs is not None
        
        doc_node = root.find("Document")
        assert doc_node is not None
        assert doc_node.get("File") == "Document.xhtml"
        assert doc_node.get("DocPath") == os.path.abspath(os.path.join(tmpdir, "mag_proj Files", "Document.xhtml"))






