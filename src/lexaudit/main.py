"""
Main entry point for LexAudit - Load data and run pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from lexaudit.config.settings import SETTINGS
from lexaudit.core.pipeline import LexAuditPipeline

logger = logging.getLogger(__name__)


def load_stj_sample(file_path: str) -> List[Dict]:
    """
    Load STJ sample data from JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of documents with their legislative references
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract relevant information for our pipeline
    documents = []
    for item in data:
        doc = {
            "id": item.get("id", "unknown"),
            "numero_processo": item.get("numeroProcesso", ""),
            "citations": item.get("referenciasLegislativas", []),
            "inteiroTeor": item.get("inteiroTeor", ""),
            "metadata": {
                "ementa": item.get("ementa", ""),
                "data_decisao": item.get("dataDecisao", ""),
                "ministro_relator": item.get("ministroRelator", ""),
            },
        }
        documents.append(doc)

    return documents


def main():
    # Load .env from config directory
    load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")

    """Main execution function."""
    # Configure logging from settings
    level_name = getattr(SETTINGS, "logging_level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level)
    logger.info("%s", "=" * 80)
    logger.info("LexAudit - Legal Citation Validation Pipeline")
    logger.info("%s", "=" * 80)
    logger.info("")

    # Configuration
    data_path = (
        Path(__file__).parent.parent.parent
        / "data"
        / "cleaned"
        / "stj"
        / "sample_10_with_fulltext.json"
    )

    logger.info("Loading data from: %s", data_path)
    logger.info("")

    # Load data
    try:
        documents = load_stj_sample(str(data_path))
        logger.info("Loaded %d documents", len(documents))
        logger.info("")
    except Exception as e:
        logger.error("Failed to load data: %s", e)
        return

    # Initialize pipeline
    logger.info("Initializing pipeline...")
    pipeline = LexAuditPipeline()
    logger.info("")

    # Process first document as test
    logger.info("Processing first document as test...")
    logger.info("%s", "-" * 80)

    if documents:
        first_doc = documents[0]
        logger.info("Document ID: %s", first_doc["id"])
        logger.info("Process Number: %s", first_doc["numero_processo"])
        logger.info("Number of legislative references: %d", len(first_doc["citations"]))
        logger.info("")

        # Show first few citations
        logger.info("First 3 citations:")
        for i, citation in enumerate(first_doc["citations"][:3], 1):
            # Truncate long citations
            citation_preview = (
                citation[:100] + "..." if len(citation) > 100 else citation
            )
            logger.info("  %d. %s", i, citation_preview)
        logger.info("")

        # Run pipeline
        result = pipeline.process_document(
            document_id=first_doc["id"],
            text=first_doc.get("inteiroTeor"),
            pre_extracted_citations=first_doc["citations"],
        )

        logger.info("")
        logger.info("%s", "=" * 80)
        logger.info("Pipeline execution completed!")
        logger.info("Results: %s", result)
        logger.info("%s", "=" * 80)
    else:
        logger.error("No documents found in the data file.")


if __name__ == "__main__":
    main()
