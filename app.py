import os
import re
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import pdfplumber


def select_pdf_file():
    """Opens a file dialog window to select a local PDF file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="Select Attendance PDF File",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
    )
    return file_path


def parse_elevation_pdf(pdf_path):
    """Parses ELEVATION 2.0 participant roster PDF headers to aggregate metrics."""
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError("No valid PDF file was selected.")

    records = []
    current_zone = "UNKNOWN ZONE"
    current_region = "UNKNOWN REGION"

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line_str = line.strip()

                # 1. Capture Zone Header (e.g., "GT ACCRA METRO ZONE")
                if re.search(r"\bZONE\b$", line_str, re.IGNORECASE) and not line_str.startswith("Organised"):
                    current_zone = line_str.replace("ZONE", "").strip()
                    continue

                # 2. Capture Region Header (e.g., "MADINA REGION · 416 registered...")
                if "REGION" in line_str.upper():
                    region_part = re.split(r"[·\-\(]", line_str)[0]
                    current_region = region_part.replace("REGION", "").strip()
                    continue

                # 3. Capture Division Header & Metrics (e.g., "Dodowa — 21 registered (6 paid, 15 pending)")
                div_match = re.search(
                    r"^(.*?)\s*[\—\–\-]\s*\d+\s+registered\s*\(\s*(\d+)\s+paid\s*,\s*(\d+)\s+pending\s*\)",
                    line_str,
                    re.IGNORECASE,
                )
                if div_match:
                    division_name = div_match.group(1).strip()
                    paid_count = int(div_match.group(2))
                    pending_count = int(div_match.group(3))

                    records.append({
                        "Zone": current_zone,
                        "Region": current_region,
                        "Division": division_name,
                        "Paid": paid_count,
                        "Pending": pending_count,
                    })

    if not records:
        raise ValueError(
            "Could not parse division headers from PDF. Ensure the document follows the ELEVATION format."
        )

    # Convert to DataFrame and aggregate duplicate divisions if split across pages
    df = pd.DataFrame(records)
    df = (
        df.groupby(["Zone", "Region", "Division"], as_index=False)[["Paid", "Pending"]]
        .sum()
    )
    return df


def process_attendance_data(df):
    """Calculates summary attendance metrics."""
    df["Registered"] = df["Paid"] + df["Pending"]
    df["Paid_Pct"] = ((df["Paid"] / df["Registered"]) * 100).fillna(0).round(1)
    df["Pending_Pct"] = ((df["Pending"] / df["Registered"]) * 100).fillna(0).round(1)
    return df


def export_to_excel(df):
    """Exports Division, Region, and Overall summaries into an Excel workbook in the Downloads folder."""
    user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    output_path = os.path.join(user_downloads, "Attendance_Summary_Report.xlsx")

    # 1. Division Breakdown DataFrame
    div_cols = [
        "Zone",
        "Region",
        "Division",
        "Registered",
        "Paid",
        "Paid_Pct",
        "Pending",
        "Pending_Pct",
    ]
    division_df = df[div_cols]

    # 2. Region Summary DataFrame
    region_df = (
        df.groupby(["Zone", "Region"])[["Registered", "Paid", "Pending"]]
        .sum()
        .reset_index()
    )
    region_df["Paid_Pct"] = (
        ((region_df["Paid"] / region_df["Registered"]) * 100).fillna(0).round(1)
    )
    region_df["Pending_Pct"] = (
        ((region_df["Pending"] / region_df["Registered"]) * 100).fillna(0).round(1)
    )
    reg_cols = [
        "Zone",
        "Region",
        "Registered",
        "Paid",
        "Paid_Pct",
        "Pending",
        "Pending_Pct",
    ]
    region_df = region_df[reg_cols]

    # 3. Overall Summary DataFrame
    total_reg = int(df["Registered"].sum())
    total_paid = int(df["Paid"].sum())
    total_pending = int(df["Pending"].sum())

    overall_paid_pct = (
        round((total_paid / total_reg) * 100, 1) if total_reg > 0 else 0
    )
    overall_pending_pct = (
        round((total_pending / total_reg) * 100, 1) if total_reg > 0 else 0
    )

    overall_df = pd.DataFrame([
        {
            "Metric": "Total Registered",
            "Count": total_reg,
            "Percentage": "100.0%"
        },
        {
            "Metric": "Total Paid",
            "Count": total_paid,
            "Percentage": f"{overall_paid_pct}%"
        },
        {
            "Metric": "Total Pending",
            "Count": total_pending,
            "Percentage": f"{overall_pending_pct}%"
        }
    ])

    # Write sheets to Excel file
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        division_df.to_excel(writer, sheet_name="Division Breakdown", index=False)
        region_df.to_excel(writer, sheet_name="Region Summary", index=False)
        overall_df.to_excel(writer, sheet_name="Overall Summary", index=False)

    print("\n" + "=" * 80)
    print(f"EXCEL REPORT SUCCESSFULLY SAVED TO:\n{output_path}")
    print("=" * 80)


def display_summaries(df):
    """Prints Division, Region, and Overall Attendance Summaries to Terminal."""
    print("=" * 80)
    print("1. ATTENDANCE BREAKDOWN BY DIVISION")
    print("=" * 80)
    div_cols = [
        "Zone",
        "Region",
        "Division",
        "Registered",
        "Paid",
        "Paid_Pct",
        "Pending",
        "Pending_Pct",
    ]
    print(df[div_cols].to_string(index=False))

    print("\n" + "=" * 80)
    print("2. ATTENDANCE BREAKDOWN BY REGION")
    print("=" * 80)
    region_df = (
        df.groupby(["Zone", "Region"])[["Registered", "Paid", "Pending"]]
        .sum()
        .reset_index()
    )
    region_df["Paid_Pct"] = (
        ((region_df["Paid"] / region_df["Registered"]) * 100).fillna(0).round(1)
    )
    region_df["Pending_Pct"] = (
        ((region_df["Pending"] / region_df["Registered"]) * 100).fillna(0).round(1)
    )
    print(region_df.to_string(index=False))

    print("\n" + "=" * 80)
    print("3. OVERALL ATTENDANCE SUMMARY")
    print("=" * 80)
    total_reg = df["Registered"].sum()
    total_paid = df["Paid"].sum()
    total_pending = df["Pending"].sum()

    overall_paid_pct = (
        round((total_paid / total_reg) * 100, 1) if total_reg > 0 else 0
    )
    overall_pending_pct = (
        round((total_pending / total_reg) * 100, 1) if total_reg > 0 else 0
    )

    print(f"Total Registered : {total_reg:,}")
    print(f"Total Paid       : {total_paid:,} ({overall_paid_pct}%)")
    print(f"Total Pending    : {total_pending:,} ({overall_pending_pct}%)")


if __name__ == "__main__":
    try:
        selected_pdf = select_pdf_file()
        if selected_pdf:
            print(f"Loading file: {selected_pdf}\n")
            df_raw = parse_elevation_pdf(selected_pdf)
            df_attendance = process_attendance_data(df_raw)

            # Display summaries on terminal
            display_summaries(df_attendance)

            # Export Excel with Division, Region, and Overall Summary sheets
            export_to_excel(df_attendance)
        else:
            print("No file selected.")

    except Exception as e:
        print(f"Error processing PDF: {e}")