
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

POLICY_DIR = Path("policies")
OUTPUT_DIR = Path("database")
OUTPUT_DIR.mkdir(exist_ok=True)

NAMESPACE = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
}


def extract_docx(filepath):

    with zipfile.ZipFile(filepath, "r") as docx:

        xml_content = docx.read("word/document.xml")

    root = ET.fromstring(xml_content)

    body = root.find("w:body", NAMESPACE)

    sections = []

    for element in body:

        tag = element.tag.split("}")[-1]

        if tag == "p":
            text = "".join(
                node.text or ""
                for node in element.findall(".//w:t", NAMESPACE)
            )

            if text.strip():
                sections.append(text)

        elif tag == "tbl":

            for row in element.findall("w:tr", NAMESPACE):

                cells = []

                for cell in row.findall("w:tc", NAMESPACE):
                    cell_text = "".join(
                        node.text or ""
                        for node in cell.findall(".//w:t", NAMESPACE)
                    )
                    cells.append(cell_text)

                sections.append(" | ".join(cells))

    return "\n".join(sections)


def main():

    files = list(POLICY_DIR.glob("*.docx"))

    if not files:
        print("ERROR: No Word policy documents found!")
        return

    all_policies = []

    for filepath in files:

        print(f"\nProcessing: {filepath.name}")

        text = extract_docx(filepath)

        all_policies.append(
            f"\n\n{'=' * 60}\n"
            f"POLICY: {filepath.stem}\n"
            f"{'=' * 60}\n{text}"
        )

        print("Extracted characters:", len(text))

    output_file = OUTPUT_DIR / "all_policies.txt"

    output_file.write_text(
        "\n".join(all_policies),
        encoding="utf-8"
    )

    print("\nAll policies extracted successfully!")
    print("Saved to:", output_file)


if __name__ == "__main__":
    main()
