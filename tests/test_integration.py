"""Integration tests for full pipeline."""

import json
import pytest
from pathlib import Path
from schemaorg_rocrate_parser import SchemaOrgParser, ISAROCrateBuilder


class TestFullPipeline:
    """End-to-end pipeline tests."""

    @pytest.mark.parametrize("example_file", [
        "example_bonares.json",
        "example_edal.json",
        "example_openagrar.json",
        "example_plabipd.json",
        "example_publisso.json",
    ])
    def test_full_pipeline_all_examples(self, examples_dir, example_file, tmp_output):
        """Run parse → build → save, verify valid ro-crate-metadata.json."""
        # Parse
        parser = SchemaOrgParser()
        parsed = parser.parse_file(examples_dir / example_file)
        
        # Build
        builder = ISAROCrateBuilder()
        crate = builder.build_from_parsed_data(parsed)
        
        # Save to tmp output
        output_path = tmp_output / example_file.replace(".json", "")
        crate.write(output_path)
        
        # Verify ro-crate-metadata.json exists and is valid
        metadata_file = output_path / "ro-crate-metadata.json"
        assert metadata_file.exists(), f"Missing {metadata_file}"
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        assert "@graph" in metadata
        assert len(metadata["@graph"]) >= 2