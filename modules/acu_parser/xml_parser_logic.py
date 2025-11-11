# xml_parser_logic.py
from lxml import etree as ET
import re
import pandas as pd
import html


def clean_html_content(content: str) -> str:
    """Cleans and formats HTML content from documentation."""
    if not content:
        return ""
    
    # Extract CDATA content if present
    cdata_match = re.search(r'<!\[CDATA\[(.*?)\]\]>', content, re.DOTALL)
    if cdata_match:
        content = cdata_match.group(1)
    
    # --- Convert HTML to plain text ---
    # Replace line breaks and paragraph ends with newlines for readability
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</p>', '\n\n', content, flags=re.IGNORECASE)
    
    # Strip all other HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Decode HTML entities (e.g., &lt; becomes <)
    content = html.unescape(content)
    
    # Clean up excess whitespace
    return '\n'.join(line.strip() for line in content.strip().split('\n'))


def _parse_xsd_for_docs(xsd_content: str) -> dict:
    """Parses an XSD file to extract documentation for each element.
    
    Returns a dictionary mapping element names to their HTML documentation strings.
    """
    if not xsd_content:
        print("⚠️ _parse_xsd_for_docs: No XSD content provided")
        return {}
    
    print(f"📖 _parse_xsd_for_docs: Processing XSD ({len(xsd_content)} characters)")
    
    try:
        docs = {}
        
        # Define XML namespaces commonly found in XSD files
        namespaces = {
            'xs': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        }
        
        # Use a lenient parser that can recover from minor errors
        parser = ET.XMLParser(remove_blank_text=True, recover=True, resolve_entities=False)
        root = ET.fromstring(xsd_content.encode('utf-8'), parser=parser)
        
        print(f"✓ Parsed XSD root: {root.tag}")
        
        # Update namespaces with any additional ones found in the document
        for prefix, uri in root.nsmap.items():
            if prefix is not None and prefix not in namespaces:
                namespaces[prefix] = uri
        
        # Find all element definitions in the XSD
        xpath_queries = [
            './/xs:element[@name]',
            './/element[@name]'
        ]
        
        elements = []
        for query in xpath_queries:
            try:
                found = root.xpath(query, namespaces=namespaces)
                elements.extend(found)
                if found:
                    print(f"✓ Query '{query}' found {len(found)} elements")
            except Exception as e:
                print(f"⚠️ Query '{query}' failed: {e}")
        
        print(f"✓ Total elements found: {len(elements)}")
        
        for element in elements:
            # Get the element's name attribute
            element_name = element.get('name')
            if not element_name:
                continue
            
            # Clean the name (remove namespace prefixes if present)
            element_name = element_name.split('}')[-1] if '}' in element_name else element_name
            element_name = element_name.split(':')[-1] if ':' in element_name else element_name
            
            # Look for annotation within this element
            annotation_paths = [
                './xs:annotation',
                './annotation',
                './/xs:annotation',
                './/annotation'
            ]
            
            annotation = None
            for anno_path in annotation_paths:
                try:
                    annotations = element.xpath(anno_path, namespaces=namespaces)
                    if annotations:
                        annotation = annotations[0]
                        break
                except Exception:
                    continue
            
            if annotation is None:
                continue
            
            # Extract documentation from the annotation
            doc_paths = [
                './xs:documentation',
                './documentation',
                './/xs:documentation',
                './/documentation'
            ]
            
            documentation_element = None
            for doc_path in doc_paths:
                try:
                    doc_elements = annotation.xpath(doc_path, namespaces=namespaces)
                    if doc_elements:
                        documentation_element = doc_elements[0]
                        break
                except Exception:
                    continue
            
            if documentation_element is None:
                continue
            
            # Extract the inner content of the documentation element
            doc_content = ET.tostring(documentation_element, encoding='unicode', method='xml')
            
            # Remove the outer documentation tag to get just the inner content
            doc_content = re.sub(r'<[^:>]*:?documentation[^>]*>', '', doc_content, count=1)
            doc_content = re.sub(r'</[^:>]*:?documentation>', '', doc_content, count=1)
            
            # Clean the content using our helper function
            doc_content = clean_html_content(doc_content)
            
            if doc_content:
                docs[element_name] = doc_content
                print(f"  ✓ Found doc for '{element_name}': {doc_content[:80]}...")
        
        print(f"✅ Extracted documentation for {len(docs)} elements")
        return docs
        
    except ET.ParseError as e:
        print(f"❌ XSD Parse Error: {e}")
        return {}
    except Exception as e:
        print(f"❌ XSD Processing Error: {e}")
        import traceback
        traceback.print_exc()
        return {}


def parse_xml_to_dataframe(xml_content: str, filename: str, xsd_content: str = None) -> pd.DataFrame:
    """Parses XML content and returns a DataFrame with parameters and their details.
    
    Args:
        xml_content: The XML content to parse
        filename: The source filename
        xsd_content: Optional XSD content for documentation extraction
        
    Returns:
        A pandas DataFrame with columns: Parameter, Value, Details, Source
    """
    if not xml_content:
        print("❌ parse_xml_to_dataframe: No XML content provided")
        return pd.DataFrame()
    
    print(f"\n{'='*60}")
    print(f"📖 Parsing XML: {filename}")
    print(f"  XML size: {len(xml_content)} characters")
    print(f"  XSD provided: {'YES' if xsd_content else 'NO'}")
    if xsd_content:
        print(f"  XSD size: {len(xsd_content)} characters")
    print(f"{'='*60}")
    
    try:
        # Parse the XML
        parser = ET.XMLParser(remove_blank_text=True, recover=True)
        root = ET.fromstring(xml_content.encode('utf-8'), parser=parser)
        
        # Extract documentation from XSD if available
        docs_dict = {}
        if xsd_content:
            print("\n🔍 Processing XSD for documentation...")
            docs_dict = _parse_xsd_for_docs(xsd_content)
            print(f"✅ XSD processing complete: {len(docs_dict)} documented elements")
        else:
            print("\n⚠️ No XSD content - skipping documentation extraction")
        
        # Extract data from XML
        records = []
        
        # Walk through all elements in the XML
        for elem in root.iter():
            # Get the element name (parameter name)
            param_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            # Skip certain system elements
            if param_name in ['root', 'config', 'schema']:
                continue

            # Check if the element is a splitter
            is_splitter = param_name.upper().endswith('_SPLITTER')
            value = elem.text.strip() if elem.text else ""

            # Skip non-splitter elements that have no value
            if not is_splitter and not value:
                continue
            
            # Get documentation from XSD if available
            details = docs_dict.get(param_name, "")
            
            # Create record
            record = {
                'Parameter': param_name,
                'Value': value,
                'Details': details
            }
            
            records.append(record)
        
        df = pd.DataFrame(records)
        
        params_with_docs = len([r for r in records if r['Details']])
        print(f"\n✅ Parsing complete:")
        print(f"   Total parameters: {len(df)}")
        print(f"   With documentation: {params_with_docs}")
        print(f"{'='*60}\n")
        
        return df
        
    except Exception as e:
        print(f"❌ XML Parse Error: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()