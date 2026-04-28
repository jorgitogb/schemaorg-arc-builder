"""Tests for SchemaOrgParser."""

import pytest
from schemaorg_arc_builder import SchemaOrgParser


class TestParserBasic:
    """Basic parser tests."""

    def test_parse_single_entity(self):
        """Parse a minimal single entity and verify dataset output."""
        parser = SchemaOrgParser()
        result = parser.parse({"@type": "Dataset", "name": "X"})
        
        assert len(result["datasets"]) == 1
        assert result["datasets"][0]["name"] == "X"

    def test_parse_graph_structure(self):
        """Parse a graph with Dataset and Person, verify correct keys."""
        parser = SchemaOrgParser()
        result = parser.parse({
            "@context": "https://schema.org",
            "@graph": [
                {"@id": "#ds1", "@type": "Dataset", "name": "Test Dataset"},
                {"@id": "#p1", "@type": "Person", "name": "Jane Doe"}
            ]
        })
        
        assert len(result["datasets"]) == 1
        assert result["datasets"][0]["name"] == "Test Dataset"
        assert len(result["persons"]) == 1
        assert result["persons"][0]["name"] == "Jane Doe"


class TestParserPerson:
    """Person parsing tests."""

    def test_parse_person_identifiers(self):
        """Parse a Person with ORCID identifier, verify type detection."""
        parser = SchemaOrgParser()
        result = parser.parse({
            "@type": "Person",
            "name": "Jane Doe",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "orcid",
                "value": "https://orcid.org/0000-0001-2345-6789"
            }
        })
        
        person = result["persons"][0]
        assert "identifier" in person
        assert "orcid" in str(person["identifier"])


class TestParserDates:
    """Date normalization tests."""

    def test_normalize_date_iso(self):
        """ISO date string should pass through unchanged."""
        parser = SchemaOrgParser()
        result = parser._normalize_date("2012-01-01")
        
        assert result == "2012-01-01"

    def test_normalize_date_java_format(self):
        """Java date format should be converted to ISO."""
        parser = SchemaOrgParser()
        result = parser._normalize_date("Sun Jan 01 00:00:00 CET 2012")
        
        assert result == "2012-01-01"


class TestParserExamples:
    """Test parsing all example files."""

    @pytest.mark.parametrize("example_file", [
        "bonares.json",
        "edal.json",
        "openagrar.json",
        "plabipd.json",
        "publisso.json",
    ])
    def test_parse_all_examples(self, examples_dir, example_file):
        """Parse each example file and verify non-empty result."""
        parser = SchemaOrgParser()
        result = parser.parse_file(examples_dir / example_file)
        
        # At least one of these keys should have data
        has_data = any(
            len(result.get(key, [])) > 0
            for key in ["datasets", "persons", "organizations"]
        )
        assert has_data, f"No data found in {example_file}"


class TestParserGrant:
    """Grant parsing tests."""

    def test_parse_grant(self):
        """Parse a Grant entity, verify extraction of name/identifier/funder."""
        parser = SchemaOrgParser()
        result = parser.parse({
            "@type": "Grant",
            "name": "NSF Grant 12345",
            "identifier": "NSF-12345",
            "funder": {"@id": "#org1", "@type": "Organization", "name": "NSF"}
        })

        grants = result["grants"]
        assert len(grants) == 1
        grant = grants[0]
        assert grant["name"] == "NSF Grant 12345"
        assert grant["identifier"] == "NSF-12345"
        assert "funder" in grant


class TestParserValidation:
    """Input validation tests."""

    def test_invalid_context_raises(self):
        """@context without schema.org or bioschemas.org should raise ValueError."""
        parser = SchemaOrgParser()
        with pytest.raises(ValueError, match="@context does not appear"):
            parser.parse({"@context": "https://example.com", "@type": "Dataset"})

    def test_missing_graph_raises(self):
        """Input with no @type or @graph should raise ValueError."""
        parser = SchemaOrgParser()
        with pytest.raises(ValueError, match="no @type or @graph"):
            parser.parse({"name": "oops"})

    def test_invalid_type_raises(self):
        """Non-dict/non-list input should raise ValueError."""
        parser = SchemaOrgParser()
        with pytest.raises(ValueError, match="Input must be a JSON object or array"):
            parser.parse(123)

    def test_valid_schema_context_passes(self):
        """https://schema.org should pass validation."""
        parser = SchemaOrgParser()
        result = parser.parse({"@context": "https://schema.org", "@type": "Dataset", "name": "X"})
        assert len(result["datasets"]) == 1

    def test_valid_bioschemas_context_passes(self):
        """https://bioschemas.org should pass validation."""
        parser = SchemaOrgParser()
        result = parser.parse({"@context": "https://bioschemas.org", "@type": "Dataset", "name": "X"})
        assert len(result["datasets"]) == 1