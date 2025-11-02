import glob
from argparse import ArgumentParser
from pathlib import Path

from PyPDF2 import PdfMerger
from tqdm import tqdm


def main():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    parser.add_argument('-o', '--output', type=str, required=False)

    args = parser.parse_args()

    pdf_paths = sorted(glob.glob(args.input))
    path = args.output

    if path is None:
        path = Path(pdf_paths[0]).parent / f"{Path(pdf_paths[0]).stem}_merged.pdf"

    # merge PDFs
    merger = PdfMerger()
    for pdf in tqdm(pdf_paths, 'mergings pdfs'):
        merger.append(pdf)
    print("writing final pdf..", end=" ", flush=True)
    merger.write(path)
    merger.close()
    print("done.")


if __name__ == "__main__":
    main()