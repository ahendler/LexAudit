"""
Main entry point for LexAudit - Load data and run pipeline.
"""
import json
from pathlib import Path
from typing import List, Dict
from lexaudit.core.pipeline import LexAuditPipeline


def load_stj_sample(file_path: str) -> List[Dict]:
    """
    Load STJ sample data from JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of documents with their legislative references
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract relevant information for our pipeline
    documents = []
    for item in data:
        doc = {
            'id': item.get('id', 'unknown'),
            'numero_processo': item.get('numeroProcesso', ''),
            'citations': item.get('referenciasLegislativas', []),
            'metadata': {
                'ementa': item.get('ementa', ''),
                'data_decisao': item.get('dataDecisao', ''),
                'ministro_relator': item.get('ministroRelator', '')
            }
        }
        documents.append(doc)

    return documents


def main():
    """Main execution function."""
    print("=" * 80)
    print("LexAudit - Legal Citation Validation Pipeline")
    print("=" * 80)
    print()

    # Configuration
    data_path = Path(__file__).parent.parent.parent / "data" / \
        "cleaned" / "stj" / "sample_10_with_fulltext.json"

    print(f"Loading data from: {data_path}")
    print()

    # Load data
    try:
        documents = load_stj_sample(str(data_path))
        print(f"Loaded {len(documents)} documents")
        print()
    except Exception as e:
        print(f"ERROR: Failed to load data: {e}")
        return

    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = LexAuditPipeline()
    print()

    # Process first document as test
    print("Processing first document as test...")
    print("-" * 80)

    if documents:
        first_doc = documents[0]
        print(f"Document ID: {first_doc['id']}")
        print(f"Process Number: {first_doc['numero_processo']}")
        print(
            f"Number of legislative references: {len(first_doc['citations'])}")
        print()

        # Show first few citations
        print("First 3 citations:")
        for i, citation in enumerate(first_doc['citations'][:3], 1):
            # Truncate long citations
            citation_preview = citation[:100] + \
                "..." if len(citation) > 100 else citation
            print(f"  {i}. {citation_preview}")
        print()

        # Run pipeline
        result = pipeline.process_document(
            document_id=first_doc['id'],
            pre_extracted_citations=first_doc['citations']
        )

        print()
        print("=" * 80)
        print("Pipeline execution completed!")
        print(f"Results: {result}")
        print("=" * 80)
    else:
        print("No documents found in the data file.")


if __name__ == "__main__":
    main()
