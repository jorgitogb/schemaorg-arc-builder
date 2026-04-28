"""Tests for ISAROCrateBuilder."""

import pytest
from schemaorg_rocrate_parser import SchemaOrgParser, ISAROCrateBuilder


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