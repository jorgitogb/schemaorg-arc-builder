"""Tests for ISAROCrateBuilder."""

import pytest
from schemaorg_arc_builder import SchemaOrgParser, ISAROCrateBuilder


class TestROCratesBuilder:
    """Tests for RO-Crate builder."""

    def test_build_minimal(self):
        """Parse minimal dataset, build crate, verify root_dataset name."""
        parser = SchemaOrgParser()
        parsed = parser.parse({"@type": "Dataset", "name": "Test Dataset"})
        
        builder = ISAROCrateBuilder()
        crate = builder.build_from_parsed_data(parsed)
        
        assert crate.root_dataset is not None
        assert crate.root_dataset["name"] == "Test Dataset"

    def test_person_dedup(self):
        """Two identical persons - currently both added (dedup not implemented - TD-3)."""
        parser = SchemaOrgParser()
        parsed = parser.parse({
            "@context": "https://schema.org",
            "@graph": [
                {"@id": "#p1", "@type": "Person", "name": "Jane Doe"},
                {"@id": "#p2", "@type": "Person", "name": "Jane Doe"}
            ]
        })
        
        builder = ISAROCrateBuilder()
        crate = builder.build_from_parsed_data(parsed)
        
        # Currently 2 persons (dedup not implemented - TD-3)
        persons = [e for e in crate.get_entities() if e.type == "Person"]
        assert len(persons) == 2

    def test_organization_added(self):
        """Organization entity should appear in the crate."""
        parser = SchemaOrgParser()
        parsed = parser.parse({
            "@type": "Organization",
            "name": "Test Institute"
        })
        
        builder = ISAROCrateBuilder()
        crate = builder.build_from_parsed_data(parsed)
        
        # Find organization in the crate
        orgs = [e for e in crate.get_entities() if e.type == "Organization"]
        assert len(orgs) >= 1

    def test_add_grant(self):
        """Add a Grant entity, verify it appears in crate with @type: Grant."""
        builder = ISAROCrateBuilder()
        grant_data = {
            '@id': '#grant1',
            'name': 'Test Grant',
            'identifier': 'GRANT-001',
            'description': 'A test grant'
        }
        result = builder._add_grant(grant_data)

        assert result is not None
        assert result['@id'] == '#grant1'

        crate_json = builder.to_json()
        graph = crate_json['@graph']
        grant_entities = [e for e in graph if e.get('@id') == '#grant1']
        assert len(grant_entities) == 1
        assert grant_entities[0]['@type'] == 'Grant'
        assert grant_entities[0]['name'] == 'Test Grant'