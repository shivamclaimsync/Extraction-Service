#!/usr/bin/env python3
"""
Split documents from a combined file based on presence of "chief Complaint".
Documents with "chief Complaint" go to hospital_visits, others to clinical_visits.

Usage:
    python -m extraction_service.scripts.split_documents_by_chief_complaint \\
        --input-file P-027.txt \\
        --hospital-visits-dir /path/to/hospital_visits \\
        --clinical-visits-dir /path/to/clinical_visits
"""

import argparse
import re
import sys
from pathlib import Path
import logging


def setup_logging(log_level: str = 'INFO'):
    """Configure logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def split_documents(content: str) -> list[tuple[str, str]]:
    """
    Split content into individual documents.
    Returns list of (document_id, document_content) tuples.
    """
    # Pattern to match document markers: <document_XXX>
    document_pattern = re.compile(r'<document_(\d+)>')
    
    documents = []
    matches = list(document_pattern.finditer(content))
    
    if not matches:
        # No document markers found, treat entire file as one document
        return [('single', content)]
    
    # Extract each document
    for i, match in enumerate(matches):
        doc_id = match.group(1)
        start_pos = match.start()
        
        # Find the end position (start of next document or end of file)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        doc_content = content[start_pos:end_pos].strip()
        documents.append((doc_id, doc_content))
    
    return documents


def has_chief_complaint(content: str) -> bool:
    """Check if document contains 'chief Complaint' (case-insensitive)."""
    # Case-insensitive search for "chief complaint" or "chief Complaint"
    pattern = re.compile(r'chief\s+complaint', re.IGNORECASE)
    return bool(pattern.search(content))


def save_document(content: str, doc_id: str, output_dir: Path, file_prefix: str = None):
    """Save a document to a file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if file_prefix:
        filename = f"{file_prefix}_document_{doc_id}.txt"
    else:
        filename = f"document_{doc_id}.txt"
    
    file_path = output_dir / filename
    file_path.write_text(content, encoding='utf-8')
    return file_path


def process_file(
    input_file: Path,
    hospital_visits_dir: Path,
    clinical_visits_dir: Path,
    file_prefix: str = None
):
    """Process a combined file and split documents."""
    logger = logging.getLogger(__name__)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    logger.info(f"Reading file: {input_file}")
    content = input_file.read_text(encoding='utf-8')
    
    logger.info("Splitting documents...")
    documents = split_documents(content)
    logger.info(f"Found {len(documents)} documents")
    
    hospital_count = 0
    clinical_count = 0
    
    for doc_id, doc_content in documents:
        if has_chief_complaint(doc_content):
            # Move to hospital_visits
            output_path = save_document(
                doc_content,
                doc_id,
                hospital_visits_dir,
                file_prefix
            )
            hospital_count += 1
            logger.info(f"  Document {doc_id}: Has 'chief Complaint' -> {output_path.name}")
        else:
            # Move to clinical_visits
            output_path = save_document(
                doc_content,
                doc_id,
                clinical_visits_dir,
                file_prefix
            )
            clinical_count += 1
            logger.info(f"  Document {doc_id}: No 'chief Complaint' -> {output_path.name}")
    
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total documents processed: {len(documents)}")
    logger.info(f"Documents with 'chief Complaint' (hospital_visits): {hospital_count}")
    logger.info(f"Documents without 'chief Complaint' (clinical_visits): {clinical_count}")
    logger.info("="*80)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Split documents based on presence of 'chief Complaint'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input-file',
        type=Path,
        required=True,
        help='Input file containing multiple documents (e.g., P-027.txt)'
    )
    
    parser.add_argument(
        '--hospital-visits-dir',
        type=Path,
        default=Path('/Users/claimsync/Desktop/Product/Jerimed/hospital_visits'),
        help='Directory for documents with chief Complaint'
    )
    
    parser.add_argument(
        '--clinical-visits-dir',
        type=Path,
        default=Path('/Users/claimsync/Desktop/Product/Jerimed/clinical_visits'),
        help='Directory for documents without chief Complaint'
    )
    
    parser.add_argument(
        '--file-prefix',
        type=str,
        default=None,
        help='Prefix for output filenames (e.g., P-027)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # If file_prefix not provided, use input file name without extension
    if args.file_prefix is None:
        args.file_prefix = args.input_file.stem
    
    # Process the file
    process_file(
        args.input_file,
        args.hospital_visits_dir,
        args.clinical_visits_dir,
        args.file_prefix
    )


if __name__ == '__main__':
    main()

