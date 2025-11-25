"""
Main entry point for LexAudit - Load data and run pipeline.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from lexaudit.config.settings import SETTINGS
from lexaudit.core.pipeline import LexAuditPipeline
from lexaudit.text_extraction import extract_text_from_file

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


def run_pipeline_on_file(file_path: Path):
    """Run pipeline on a single file."""
    logger.info("Processing file: %s", file_path)
    
    try:
        text = extract_text_from_file(file_path)
        logger.info("Successfully extracted %d characters", len(text))
    except Exception as e:
        logger.error("Failed to extract text: %s", e)
        return

    # Initialize pipeline
    logger.info("Initializing pipeline...")
    pipeline = LexAuditPipeline()
    
    # Run pipeline
    document_id = file_path.stem
    logger.info("Running pipeline for document ID: %s", document_id)
    
    result = pipeline.process_document(
        document_id=document_id,
        text=text,
        pre_extracted_citations=None # No pre-extracted citations for raw files
    )
    
    logger.info("%s", "=" * 80)
    logger.info("Pipeline execution completed!")
    logger.info("Results saved to data/validation_outputs/")
    logger.info("%s", "=" * 80)


def run_sample_mode():
    """Run the original sample mode."""
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


def main():
    # Load .env from config directory
    load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")

    # Configure logging from settings
    level_name = getattr(SETTINGS, "logging_level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("%s", "=" * 80)
    logger.info("LexAudit - Legal Citation Validation Pipeline")
    logger.info("%s", "=" * 80)
    logger.info("")

    parser = argparse.ArgumentParser(description="LexAudit - Legal citation extraction pipeline")
    parser.add_argument("file", nargs="?", help="Path to the file to process (txt, pdf, docx)")
    parser.add_argument("--sample", action="store_true", help="Run with internal sample data (default if no file provided)")
    
    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            sys.exit(1)
        run_pipeline_on_file(file_path)
    else:
        # Default behavior or explicit sample flag
        run_sample_mode()


if __name__ == "__main__":
    main()
