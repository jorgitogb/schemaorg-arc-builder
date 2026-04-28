"""Integration tests for full pipeline."""

import json
import pytest
from pathlib import Path
from schemaorg_arc_builder import SchemaOrgParser, ISAROCrateBuilder


class TestFullPipeline:
    """End-to-end pipeline tests."""

    @pytest.mark.parametrize("example_file", [
        "bonares.json",
        "edal.json",
        "openagrar.json",
        "plabipd.json",
        "publisso.json",
    ])
    def test_full_pipeline_all_examples(self, examples_dir, example_file, tmp_output):
        """Run parse → build → save, verify valid ro-crate-metadata.json."""
        # Parse
        parser = SchemaOrgParser()
        parsed = parser.parse_file(examples_dir / example_file)

        datasets = parsed.get('datasets', [])
        assert len(datasets) >= 1, f"No datasets in {example_file}"

        # For single dataset, use build_from_parsed_data (original behavior)
        # For multi-dataset, test build_single_dataset
        builder = ISAROCrateBuilder()

        if len(datasets) == 1:
            # Original behavior
            crate = builder.build_from_parsed_data(parsed)
            output_path = tmp_output / example_file.replace(".json", "")
        else:
            # New behavior - build first dataset
            shared_entities = {
                'persons': parsed.get('persons', []),
                'organizations': parsed.get('organizations', []),
                'grants': parsed.get('grants', []),
                'publications': parsed.get('publications', [])
            }
            crate = builder.build_single_dataset(datasets[0], shared_entities)
            dir_name, _ = builder.generate_arc_name(example_file, datasets[0])
            output_path = tmp_output / dir_name

        # Save to tmp output
        crate.write(output_path)

        # Verify ro-crate-metadata.json exists and is valid
        metadata_file = output_path / "ro-crate-metadata.json"
        assert metadata_file.exists(), f"Missing {metadata_file}"

        with open(metadata_file) as f:
            metadata = json.load(f)

        assert "@graph" in metadata
        assert len(metadata["@graph"]) >= 2