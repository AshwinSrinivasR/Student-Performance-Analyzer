
import csv
import math
from pathlib import Path
from statistics import mean

DATA_PATH = Path("data/marks.csv")
OUTPUT_DIR = Path("outputs")
PLOT_DIR = Path("plots")

EXPECTED_SUBJECTS = ["Maths", "Science", "English"]
REQUIRED_COLUMNS = ["Name"] + EXPECTED_SUBJECTS + ["StudyHours"]


def load_students(csv_path):
    """Load students from CSV. Returns list of dicts. Skips rows with missing Name or all marks invalid."""
    students = []
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing_cols:
            raise ValueError(f"CSV missing required columns: {missing_cols}")
        for row in reader:
            name = (row.get("Name") or "").strip()
            if not name:
                continue
            # parse numeric fields, treat invalid as None
            def to_num(val):
                try:
                    return float(val)
                except Exception:
                    return None
            maths = to_num(row.get("Maths"))
            science = to_num(row.get("Science"))
            english = to_num(row.get("English"))
            study = to_num(row.get("StudyHours"))
            # if all marks are None, skip
            if maths is None and science is None and english is None:
                continue
            # replace missing subject marks with subject mean later; for now store None
            students.append({
                "Name": name,
                "Maths": maths,
                "Science": science,
                "English": english,
                "StudyHours": 0.0 if study is None else study
            })
    return students


def fill_missing_subjects(students):
    """Fill missing subject values with that subject's mean (computed from available values)."""
    for subj in EXPECTED_SUBJECTS:
        vals = [s[subj] for s in students if s[subj] is not None]
        subj_mean = mean(vals) if vals else 0.0
        for s in students:
            if s[subj] is None:
                s[subj] = subj_mean


def student_average(s):
    return (s["Maths"] + s["Science"] + s["English"]) / 3.0


def class_average(students):
    avgs = [student_average(s) for s in students]
    return mean(avgs) if avgs else 0.0


def top_performer(students):
    best = max(students, key=lambda s: student_average(s))
    return best["Name"], student_average(best)


def subject_averages(students):
    res = {}
    for subj in EXPECTED_SUBJECTS:
        res[subj] = mean([s[subj] for s in students]) if students else 0.0
    return res


def pearson_correlation(xs, ys):
    """Compute Pearson r for two lists of numbers. Return float('nan') if undefined."""
    n = len(xs)
    if n == 0:
        return float("nan")
    mean_x = mean(xs)
    mean_y = mean(ys)
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    den = den_x * den_y
    if den == 0:
        return float("nan")
    return num / den


def ascii_histogram(values, bins=10, width=50):
    """Return a string containing an ASCII histogram for the numeric list `values`."""
    if not values:
        return "No data to plot."
    mn, mx = min(values), max(values)
    if mn == mx:
        # single value, show a simple bar
        bar = "#" * min(width, int(round(values[0])))
        return f"{values[0]:.2f} | {bar}\n"
    bin_edges = [mn + i * (mx - mn) / bins for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        # place v in proper bin (last bin includes max)
        for i in range(bins):
            if (i < bins - 1 and bin_edges[i] <= v < bin_edges[i + 1]) or (i == bins - 1 and bin_edges[i] <= v <= bin_edges[i + 1]):
                counts[i] += 1
                break
    max_count = max(counts)
    lines = []
    for i in range(bins):
        left = bin_edges[i]
        right = bin_edges[i + 1]
        cnt = counts[i]
        bar_len = int(round((cnt / max_count) * width)) if max_count > 0 else 0
        bar = "#" * bar_len
        lines.append(f"{left:>6.2f} - {right:>6.2f} | {bar} ({cnt})")
    return "\n".join(lines)


def save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def main():
    try:
        students = load_students(DATA_PATH)
    except Exception as e:
        print("Error:", e)
        return

    if not students:
        print("No valid student rows found in CSV.")
        return

    # Fill missing subject marks with subject mean
    fill_missing_subjects(students)

    # Calculations
    total_students = len(students)
    class_avg = class_average(students)
    top_name, top_score = top_performer(students)
    subj_avgs = subject_averages(students)
    student_avgs = [student_average(s) for s in students]
    study_hours = [s["StudyHours"] for s in students]
    corr = pearson_correlation(study_hours, student_avgs)

    # Console summary
    print("\n--- Student Performance Analyzer (core Python) ---\n")
    print(f"Total students: {total_students}")
    print(f"Class average (mean of student averages): {class_avg:.2f}")
    print(f"Top performer: {top_name} ({top_score:.2f})\n")
    print("Subject-wise averages:")
    for subj, val in subj_avgs.items():
        print(f"  {subj}: {val:.2f}")
    if math.isnan(corr):
        print("\nCorrelation (StudyHours vs Average): Not defined (insufficient variation).")
    else:
        print(f"\nCorrelation (StudyHours vs Average): {corr:.2f}")

    # Save readable results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_text = []
    out_text.append("Student Performance Analyzer - Results\n")
    out_text.append(f"Total students: {total_students}\n")
    out_text.append(f"Class average: {class_avg:.2f}\n")
    out_text.append(f"Top performer: {top_name} ({top_score:.2f})\n\n")
    out_text.append("Subject-wise averages:\n")
    for subj, val in subj_avgs.items():
        out_text.append(f"  {subj}: {val:.2f}\n")
    out_text.append("\n")
    if math.isnan(corr):
        out_text.append("Correlation (StudyHours vs Average): Not defined (insufficient variation).\n")
    else:
        out_text.append(f"Correlation (StudyHours vs Average): {corr:.2f}\n")

    save_text(OUTPUT_DIR / "results.txt", "".join(out_text))
    print(f"\nResults saved to: {OUTPUT_DIR / 'results.txt'}")

    # ASCII histogram
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    hist = ascii_histogram(student_avgs, bins=10, width=50)
    hist_header = "Score Distribution (Average per Student)\n\n"
    save_text(PLOT_DIR / "score_distribution.txt", hist_header + hist)
    print(f"ASCII histogram saved to: {PLOT_DIR / 'score_distribution.txt'}")

    # Optional: Save per-student averages csv
    csv_out = OUTPUT_DIR / "results_with_average.csv"
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name"] + EXPECTED_SUBJECTS + ["StudyHours", "StudentAverage"])
        for s, avg in zip(students, student_avgs):
            writer.writerow([s["Name"], f"{s['Maths']:.2f}", f"{s['Science']:.2f}", f"{s['English']:.2f}", f"{s['StudyHours']:.2f}", f"{avg:.2f}"])
    print(f"Per-student CSV saved to: {csv_out}")

    print("\nDone.")


if __name__ == "__main__":
    main()
