"""Parser for Schema.org JSON-LD metadata."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Union
from pathlib import Path


class SchemaOrgParser:
    """Parse Schema.org JSON-LD metadata into normalized structure."""
    
    def __init__(self):
        self.context = {}
        self.graph = []
        self.all_persons = {}
        self.all_organizations = {}
    
    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Parse JSON-LD from a file.
        
        Args:
            file_path: Path to JSON-LD file
            
        Returns:
            Parsed and normalized metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.parse(data)
    
    def parse(self, data: Union[Dict, List, str]) -> Dict[str, Any]:
        """Parse JSON-LD metadata.
        
        Args:
            data: JSON-LD data (dict, list, or JSON string)
            
        Returns:
            Normalized metadata structure
        """
        if isinstance(data, str):
            data = json.loads(data)
        
        # Handle different JSON-LD structures
        if isinstance(data, list):
            # Array of entities
            return self._parse_graph(data)
        elif isinstance(data, dict):
            if '@graph' in data:
                # Named graph structure
                self.context = data.get('@context', {})
                return self._parse_graph(data['@graph'])
            else:
                # Single entity - wrap it as a single-item graph
                self.context = data.get('@context', {})
                return self._parse_graph([data])
        
        return {}
    
    def _parse_graph(self, graph: List[Dict]) -> Dict[str, Any]:
        """Parse a graph of entities.
        
        Args:
            graph: List of JSON-LD entities
            
        Returns:
            Structured metadata with entities organized by type
        """
        entities = {
            'datasets': [],
            'persons': [],
            'organizations': [],
            'publications': [],
            'other': []
        }
        
        # First pass: parse all entities
        all_parsed = []
        for entity in graph:
            parsed = self._parse_entity(entity)
            all_parsed.append(parsed)
            entity_type = self._get_type(entity)
            
            if 'Dataset' in entity_type:
                entities['datasets'].append(parsed)
            elif 'Person' in entity_type:
                entities['persons'].append(parsed)
            elif 'Organization' in entity_type:
                entities['organizations'].append(parsed)
            elif any(t in entity_type for t in ['ScholarlyArticle', 'Article', 'Publication']):
                entities['publications'].append(parsed)
            else:
                entities['other'].append(parsed)
        
        # Build id_index from first pass
        id_index: Dict[str, Dict] = {}
        for parsed in all_parsed:
            if parsed.get('@id'):
                id_index[parsed['@id']] = parsed
        
        # Second pass: resolve @id references
        for key in ['datasets', 'persons', 'organizations', 'publications', 'other']:
            for i, entity in enumerate(entities[key]):
                entities[key][i] = self._resolve_references(entity, id_index)
        
        return entities
    
    def _resolve_references(self, value: Any, id_index: Dict[str, Dict]) -> Any:
        """Resolve @id references in a value using the id_index.
        
        Args:
            value: Value to resolve (dict, list, or primitive)
            id_index: Mapping of @id -> full entity
            
        Returns:
            Value with references resolved
        """
        if isinstance(value, dict):
            # Check if it's a reference-only dict (only @id, no other keys)
            if value.keys() == {'@id'}:
                ref_id = value.get('@id', '')
                # Only resolve local references (not external URIs)
                if ref_id and not ref_id.startswith(('http://', 'https://')):
                    if ref_id in id_index:
                        return id_index[ref_id]
            # Recurse into all dict values
            return {k: self._resolve_references(v, id_index) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_references(item, id_index) for item in value]
        return value
    
    def _parse_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single entity.
        
        Args:
            entity: JSON-LD entity
            
        Returns:
            Normalized entity data
        """
        if not isinstance(entity, dict):
            return {}
        
        entity_type = self._get_type(entity)
        
        # Handle Person entities with special care for identifiers
        if 'Person' in entity_type:
            return self._parse_person(entity)
        
        # Handle Organization entities
        if 'Organization' in entity_type:
            return self._parse_organization(entity)
        
        # Extract common properties for other entities
        parsed = {
            '@id': entity.get('@id', ''),
            '@type': entity_type,
            'name': self._get_value(entity.get('name', entity.get('headline', ''))),
            'description': self._get_value(entity.get('description', '')),
        }
        
        # Add all other properties
        for key, value in entity.items():
            if key not in ['@id', '@type', '@context', 'name', 'description', 'headline']:
                # Normalize date fields
                if key in ['datePublished', 'dateCreated', 'dateModified', 'dateSubmitted', 'publicReleaseDate']:
                    if isinstance(value, str):
                        parsed[key] = self._normalize_date(value)
                    else:
                        parsed[key] = value
                # Extract value from PropertyValue objects for identifier
                elif key == 'identifier':
                    parsed[key] = self._normalize_identifier(value)
                else:
                    parsed[key] = self._normalize_value(value)
        
        return parsed
    
    def _parse_person(self, person: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Person entity with all identifier formats.
        
        Args:
            person: Person entity
            
        Returns:
            Normalized person data
        """
        person_id = person.get('@id', '')
        if not person_id:
            # Generate ID from name
            name = person.get('name', '')
            if not name:
                given = person.get('givenName', '')
                family = person.get('familyName', '')
                name = f"{given}_{family}".strip('_')
            person_id = f"#Person_{name.replace(' ', '_')}"
        
        parsed = {
            '@id': person_id,
            '@type': ['Person'],
            'name': person.get('name', ''),
            'givenName': person.get('givenName', ''),
            'familyName': person.get('familyName', ''),
        }
        
        # Handle identifiers (can be string, dict, or list)
        identifiers = person.get('identifier', [])
        if identifiers:
            parsed['identifier'] = self._parse_identifiers(identifiers)
        
        # Handle address (can be string or PostalAddress object)
        if 'address' in person:
            address = person['address']
            if isinstance(address, dict) and '@type' in address and address['@type'] == 'PostalAddress':
                # Flatten PostalAddress to string or keep as simplified object
                address_parts = []
                if address.get('streetAddress'):
                    address_parts.append(address['streetAddress'])
                if address.get('postalCode'):
                    address_parts.append(address['postalCode'])
                if address.get('addressCountry'):
                    address_parts.append(address['addressCountry'])
                parsed['address'] = ', '.join(address_parts) if address_parts else str(address)
            else:
                parsed['address'] = self._normalize_value(address)
        
        # Handle affiliation
        if 'affiliation' in person:
            parsed['affiliation'] = self._normalize_value(person['affiliation'])
        
        # Handle job title
        if 'jobTitle' in person:
            parsed['jobTitle'] = self._normalize_value(person['jobTitle'])
        
        # Handle email
        if 'email' in person:
            parsed['email'] = person['email']
        
        # Store in global person registry
        self.all_persons[person_id] = parsed
        
        return parsed
    
    def _parse_organization(self, org: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Organization entity.
        
        Args:
            org: Organization entity
            
        Returns:
            Normalized organization data
        """
        org_id = org.get('@id', '')
        if not org_id:
            name = org.get('name', 'Unknown')
            org_id = f"#Organization_{name.replace(' ', '_')[:50]}"
        
        parsed = {
            '@id': org_id,
            '@type': ['Organization'],
            'name': org.get('name', ''),
        }
        
        # Handle contact point (flatten ContactPoint objects)
        if 'contactPoint' in org:
            contact = org['contactPoint']
            if isinstance(contact, dict) and contact.get('@type') == 'ContactPoint':
                # Flatten ContactPoint to string (name and email)
                contact_parts = []
                if contact.get('name'):
                    contact_parts.append(contact['name'])
                if contact.get('email'):
                    contact_parts.append(f"({contact['email']})")
                parsed['contactPoint'] = ' '.join(contact_parts) if contact_parts else str(contact)
            else:
                parsed['contactPoint'] = self._normalize_value(contact)
        
        # Handle email
        if 'email' in org:
            parsed['email'] = org['email']
        
        # Handle url
        if 'url' in org:
            parsed['url'] = org['url']
        
        # Handle address
        if 'address' in org:
            address = org['address']
            if isinstance(address, dict) and '@type' in address and address['@type'] == 'PostalAddress':
                # Flatten PostalAddress to string
                address_parts = []
                if address.get('streetAddress'):
                    address_parts.append(address['streetAddress'])
                if address.get('postalCode'):
                    address_parts.append(address['postalCode'])
                if address.get('addressCountry'):
                    address_parts.append(address['addressCountry'])
                parsed['address'] = ', '.join(address_parts) if address_parts else str(address)
            else:
                parsed['address'] = self._normalize_value(address)
        
        # Store in global organization registry
        self.all_organizations[org_id] = parsed
        
        return parsed
    
    def _parse_identifiers(self, identifiers: Union[str, Dict, List]) -> List[Dict[str, str]]:
        """Parse various identifier formats.
        
        Args:
            identifiers: Identifier in various formats
            
        Returns:
            List of normalized identifiers
        """
        result = []
        
        if isinstance(identifiers, str):
            # Single string identifier (URL)
            result.append({'@id': identifiers, 'type': self._identify_identifier_type(identifiers)})
        elif isinstance(identifiers, dict):
            # Single PropertyValue or simple dict
            if 'propertyID' in identifiers:
                # PropertyValue - extract to simple dict without @type
                result.append({
                    '@id': identifiers.get('value', ''),  # Store value as @id for rocrate compatibility
                    'propertyID': identifiers['propertyID'],
                    'value': identifiers.get('value', '')
                })
            elif '@id' in identifiers:
                result.append({'@id': identifiers['@id']})
            else:
                result.append(identifiers)
        elif isinstance(identifiers, list):
            # List of identifiers (mixed formats)
            for item in identifiers:
                if isinstance(item, str):
                    result.append({'@id': item, 'type': self._identify_identifier_type(item)})
                elif isinstance(item, dict):
                    if 'propertyID' in item:
                        # PropertyValue - extract to simple dict without @type
                        result.append({
                            '@id': item.get('value', ''),  # Store value as @id for rocrate compatibility
                            'propertyID': item['propertyID'],
                            'value': item.get('value', '')
                        })
                    else:
                        result.append(item)
        
        return result
    
    def _identify_identifier_type(self, url: str) -> str:
        """Identify the type of identifier from URL.
        
        Args:
            url: Identifier URL
            
        Returns:
            Type of identifier
        """
        if 'orcid.org' in url:
            return 'orcid'
        elif 'd-nb.info/gnd' in url:
            return 'gnd'
        elif 'viaf.org' in url:
            return 'viaf'
        elif 'doi.org' in url or url.startswith('10.'):
            return 'doi'
        return 'url'
    
    def _get_type(self, entity: Dict) -> List[str]:
        """Extract type(s) from entity.
        
        Args:
            entity: JSON-LD entity
            
        Returns:
            List of types
        """
        entity_type = entity.get('@type', [])
        if isinstance(entity_type, str):
            return [entity_type]
        return entity_type if isinstance(entity_type, list) else []
    
    def _get_value(self, value: Any) -> Any:
        """Extract value from potentially complex structures.
        
        Args:
            value: Property value
            
        Returns:
            Simplified value
        """
        if isinstance(value, dict):
            if '@value' in value:
                return value['@value']
            if '@id' in value:
                return value['@id']
        return value
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalize complex values recursively.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized value
        """
        if isinstance(value, dict):
            # Don't convert reference-only dicts (only @id) - those need to be resolved later
            if value.keys() == {'@id'}:
                return value
            if '@value' in value or '@id' in value:
                return self._get_value(value)
            # Check if it's a Person or Organization entity
            entity_type = value.get('@type', '')
            if isinstance(entity_type, str):
                if entity_type == 'Person':
                    return self._parse_person(value)
                elif entity_type == 'Organization':
                    return self._parse_organization(value)
                elif entity_type == 'Place':
                    # Flatten Place to string (extract geo coordinates if available)
                    geo = value.get('geo', {})
                    if isinstance(geo, dict) and geo.get('@type') == 'GeoShape':
                        box = geo.get('box', '')
                        if box:
                            return f"GeoShape: {box}"
                    return str(value)
                elif entity_type in ['ContactPoint', 'GeoShape', 'DataCatalog']:
                    # Flatten complex objects without @id - extract name if available
                    name = value.get('name', '')
                    if name:
                        return name
                    return str(value)
            elif isinstance(entity_type, list):
                if 'Person' in entity_type:
                    return self._parse_person(value)
                elif 'Organization' in entity_type:
                    return self._parse_organization(value)
            # Otherwise normalize recursively
            return {k: self._normalize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._normalize_value(v) for v in value]
        return value
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date strings to ISO 8601 format (YYYY-MM-DD).
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO 8601 formatted date string
        """
        if not isinstance(date_str, str):
            return str(date_str)
        
        # Already in ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
            return date_str.split('T')[0]  # Remove time if present
        
        # Handle Java toString() format: "Sun Jan 01 00:00:00 CET 2012"
        # Pattern: DDD MMM DD HH:MM:SS ZZZ YYYY
        match = re.match(r'\w{3}\s+(\w{3})\s+(\d{2})\s+\d{2}:\d{2}:\d{2}\s+\w+\s+(\d{4})', date_str)
        if match:
            month_name, day, year = match.groups()
            try:
                # Parse using datetime
                date_obj = datetime.strptime(f"{month_name} {day} {year}", "%b %d %Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # Try parsing common formats
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y%m%d",
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # Return original if no format matches
        return date_str
    
    def _normalize_identifier(self, identifier: Any) -> Any:
        """Normalize identifier field, extracting value from PropertyValue objects.
        
        Args:
            identifier: Identifier value (string, dict, or list)
            
        Returns:
            Normalized identifier (extracts 'value' from PropertyValue)
        """
        if isinstance(identifier, dict):
            # If it's a PropertyValue, extract the value
            if identifier.get('@type') == 'PropertyValue':
                return identifier.get('value', identifier.get('url', str(identifier)))
            # If it has @id, use that
            elif '@id' in identifier:
                return identifier['@id']
            # Otherwise return as-is
            return identifier
        elif isinstance(identifier, list):
            # Process each item in the list
            result = []
            for item in identifier:
                if isinstance(item, dict) and item.get('@type') == 'PropertyValue':
                    result.append(item.get('value', item.get('url', str(item))))
                elif isinstance(item, dict) and '@id' in item:
                    result.append(item['@id'])
                elif isinstance(item, str):
                    result.append(item)
                else:
                    result.append(item)
            # Return first non-empty value if list
            return next((v for v in result if v), result)
        else:
            # Return as-is for strings and other types
            return identifier

