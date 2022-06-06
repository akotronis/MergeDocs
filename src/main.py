import os
from pathlib import Path

from classes import PdfMerger


if __name__ == '__main__':
    # Using os
    tests_folder = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)), 'tests')
    # Using pathlib
    tests_folder = Path(__file__).resolve().parent.parent / 'tests'

    init_path = tests_folder / 'Book'

    pdfm = PdfMerger(
        init_path=init_path,
        # watermark_file_path=tests_folder / 'watermark.pdf',
    )

    print(pdfm.string_tree)
    pdfm.merge_files()