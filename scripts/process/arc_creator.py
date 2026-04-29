"""Create ARC structures from ISA RO-Crate using ARCtrl Python bindings."""

import argparse
import json
import logging
import re
from pathlib import Path

from arctrl import ARC

logger = logging.getLogger(__name__)


class ARCCreator:
    """Create ARC structures from RO-Crate metadata using ARCtrl."""
    
    def __init__(self, rocrate_path: Path = None):
        """Initialize ARC creator.
        
        Args:
            rocrate_path: Path to ro-crate-metadata.json file (optional)
        """
        self.rocrate_path = rocrate_path
        self.output_dir = rocrate_path.parent if rocrate_path else Path('.')
        self.arc_identifier = None
        
    def create_arc(self) -> ARC:
        """Create ARC from RO-Crate metadata using ARCtrl.
        
        Returns:
            ARC object
        """
        # Load RO-Crate JSON
        with open(self.rocrate_path, 'r', encoding='utf-8') as f:
            rocrate_json_string = f.read()
            rocrate_data = json.loads(rocrate_json_string)
        
        # Create ARC from RO-Crate JSON using ARCtrl
        arc = ARC.from_rocrate_json_string(rocrate_json_string)
        
        # ARCtrl's from_rocrate_json_string doesn't automatically map date fields
        # So we need to manually set them from the RO-Crate metadata
        investigation_entity = next(
            (e for e in rocrate_data.get('@graph', []) if e.get('@id') == './'),
            None
        )
        
        if investigation_entity:
            # Set dates if they exist in the RO-Crate
            if 'submissionDate' in investigation_entity:
                arc.SubmissionDate = investigation_entity['submissionDate']
            if 'publicReleaseDate' in investigation_entity:
                arc.PublicReleaseDate = investigation_entity['publicReleaseDate']
                
            # Add DOI as comment
            original_identifier = investigation_entity.get('identifier', '')
            if original_identifier:
                from arctrl import Comment
                doi_comment = Comment('DOI', original_identifier)
                arc.Comments.append(doi_comment)
                
            # Handle Organization creators (ARCtrl only maps Person, not Organization)
            # Convert Organizations to Person contacts
            self._add_organization_contacts(arc, investigation_entity, rocrate_data)
        
    def create_arc_from_dict(self, rocrate_data: dict, limit: Optional[int] = None) -> ARC:
        """Create ARC from RO-Crate metadata dictionary.
        
        Args:
            rocrate_data: RO-Crate metadata dictionary
            limit: Limit number of datasets to process (default: no limit)
            
        Returns:
            ARC object
        """
        # Apply dataset limit if specified
        if limit:
            # Limit datasets in the RO-Crate data to first 'limit' datasets
            # We'll modify the @graph to include only datasets up to the limit
            graph = rocrate_data.get('@graph', [])
            
            # Find datasets in the graph (entities with @type = 'Dataset')
            datasets = [item for item in graph if item.get('@type') == 'Dataset']
            
            # Limit datasets if needed
            if len(datasets) > limit:
                # Keep the first 'limit' datasets and their related entities
                dataset_ids = [dataset.get('@id') for dataset in datasets[:limit]]
                
                # Keep root entity, dataset entities, and related entities
                filtered_graph = []
                for item in graph:
                    # Always keep the root entity
                    if item.get('@id') == './':
                        filtered_graph.append(item)
                        continue
                    
                    # Keep the dataset itself
                    if item.get('@id') in dataset_ids:
                        filtered_graph.append(item)
                        continue
                        
                    # Keep entities that reference datasets (like creator links, etc.)
                    # This is a simplified approach - we could be more sophisticated
                    filtered_graph.append(item)
                
                rocrate_data['@graph'] = filtered_graph
        
        # Convert dict to JSON string
        import json
        rocrate_json_string = json.dumps(rocrate_data)
        
        # Create ARC from RO-Crate JSON using ARCtrl
        arc = ARC.from_rocrate_json_string(rocrate_json_string)
        
        # ARCtrl's from_rocrate_json_string doesn't automatically map date fields
        # So we need to manually set them from the RO-Crate metadata
        investigation_entity = next(
            (e for e in rocrate_data.get('@graph', []) if e.get('@id') == './'),
            None
        )
        
        if investigation_entity:
            # Set dates if they exist in the RO-Crate
            if 'submissionDate' in investigation_entity:
                arc.SubmissionDate = investigation_entity['submissionDate']
            if 'publicReleaseDate' in investigation_entity:
                arc.PublicReleaseDate = investigation_entity['publicReleaseDate']
                
            # Add DOI as comment
            original_identifier = investigation_entity.get('identifier', '')
            if original_identifier:
                from arctrl import Comment
                doi_comment = Comment('DOI', original_identifier)
                arc.Comments.append(doi_comment)
                
            # Handle Organization creators (ARCtrl only maps Person, not Organization)
            # Convert Organizations to Person contacts
            self._add_organization_contacts(arc, investigation_entity, rocrate_data)
        
        return arc
    
    def _add_organization_contacts(self, arc: ARC, investigation_entity: dict, rocrate_data: dict):
        """Add Organization entities as Person contacts to Investigation.
        
        Args:
            arc: ARC object
            investigation_entity: Investigation entity from RO-Crate
            rocrate_data: Complete RO-Crate data
        """
        from arctrl import Person
        
        # Get all graph entities for lookup
        entities_by_id = {e.get('@id'): e for e in rocrate_data.get('@graph', [])}
        
        # Check creators for Organizations
        creators = investigation_entity.get('creator', [])
        if not isinstance(creators, list):
            creators = [creators]
        
        for creator_ref in creators:
            if isinstance(creator_ref, dict):
                creator_id = creator_ref.get('@id', '')
                creator_entity = entities_by_id.get(creator_id, {})
                
                # If it's an Organization, create a Person contact from it
                if creator_entity.get('@type') == 'Organization':
                    org_name = creator_entity.get('name', '')
                    
                    # Parse contactPoint for person name and email
                    # Format: "FirstName LastName (email@domain.com)"
                    contact_point = creator_entity.get('contactPoint', '')
                    first_name = ''
                    last_name = ''
                    email = creator_entity.get('email', '')
                    
                    if isinstance(contact_point, str) and contact_point:
                        # Extract name and email from contactPoint
                        # match = re.match(r'^(.+?)\s*\(([^)]+)\)$', contact_point)
                        if match:
                            full_name = match.group(1).strip()
                            email = match.group(2).strip()
                            
                            # Split full name into first and last
                            name_parts = full_name.split()
                            if len(name_parts) > 1:
                                first_name = ' '.join(name_parts[:-1])
                                last_name = name_parts[-1]
                            elif len(name_parts) == 1:
                                last_name = name_parts[0]
                    
                    # Use organization name as last name if no contact person found
                    if not last_name:
                        last_name = org_name
                    
                    # Create a Person with the organization as affiliation
                    person = Person(
                        last_name=last_name,
                        first_name=first_name,
                        mid_initials='',
                        email=email,
                        phone='',
                        fax='',
                        address=creator_entity.get('address', ''),
                        affiliation=org_name
                    )
                    
                    # Add to Investigation contacts if not already present
                    if person not in arc.Contacts:
                        arc.Contacts.append(person)

    
    def write_arc(self, arc: ARC, arc_name: str | None = None):
        """Write ARC to disk.
        
        Args:
            arc: ARC object to write
            arc_name: Name for the ARC directory (default: use identifier)
        """
        # Write ARC directly to output_dir (not a subdirectory)
        arc_path = self.output_dir

        # Write ARC using ARCtrl
        arc.Write(str(arc_path))
        
        logger.info(f"ARC written to: {arc_path}")
        logger.info(f"  Investigation: {arc_path / 'isa.investigation.xlsx'}")
        
        studies_dir = arc_path / 'studies'
        if studies_dir.exists():
            study_count = len(list(studies_dir.iterdir()))
            logger.info(f"  Studies: {study_count}")

        assays_dir = arc_path / 'assays'
        if assays_dir.exists():
            assay_count = len(list(assays_dir.iterdir()))
            logger.info(f"  Assays: {assay_count}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create ARC from ISA RO-Crate metadata using ARCtrl'
    )
    parser.add_argument(
        'rocrate_path',
        type=str,
        help='Path to ro-crate-metadata.json file'
    )
    parser.add_argument(
        '-n', '--name',
        type=str,
        default=None,
        help='Name for the ARC (default: use parent directory name)'
    )
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    logger.info(f"Creating ARC from: {args.rocrate_path}")
    creator = ARCCreator(Path(args.rocrate_path))
    arc = creator.create_arc()
    creator.write_arc(arc, args.name)

    logger.info("ARC creation complete")


if __name__ == '__main__':
    main()
