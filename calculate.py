from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import StringIO
from pathlib import Path


REQUIRED_COLUMNS = ["课程名称", "修读时间", "学分", "等第", "绩点"]
OPTIONAL_COLUMNS = ["课程类型", "备注"]
ALLOWED_GRADES = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "D-", "F", "P", "NP"}
EXCLUDED_GRADES = {"P", "NP", "F"}
CANONICAL_SEMESTERS = [
    "大一上",
    "大一下",
    "大二上",
    "大二下",
    "大三上",
    "大三下",
    "大四上",
    "大四下",
]
CANONICAL_SEMESTER_INDEX = {name: idx for idx, name in enumerate(CANONICAL_SEMESTERS)}


@dataclass
class Course:
    name: str
    semester: str
    credit: Decimal
    grade: str
    gpa: Decimal | None
    course_type: str = ""
    remark: str = ""


class ValidationError(ValueError):
    pass


def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def parse_decimal(value: str, field_name: str, row_index: int) -> Decimal:
    cleaned = normalize_text(value)
    if cleaned == "":
        raise ValidationError(f"第 {row_index} 行：{field_name} 为空。")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValidationError(f"第 {row_index} 行：{field_name} 不是合法数字：{cleaned}") from exc


def detect_csv_dialect_from_text(csv_text: str) -> csv.Dialect:
    sample = csv_text[:4096]
    if not sample.strip():
        raise ValidationError("CSV 文件为空。")
    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";"])
    except csv.Error:
        class _CommaDialect(csv.Dialect):
            delimiter = ","
            quotechar = '"'
            doublequote = True
            skipinitialspace = False
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL

        return _CommaDialect()


def decode_csv_bytes(raw_bytes: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValidationError("CSV 编码无法识别，请使用 UTF-8/UTF-8-SIG/GBK。")


def _validate_header(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValidationError("CSV 缺少表头。")

    missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing:
        raise ValidationError(
            "CSV 缺少必要列："
            + "、".join(missing)
            + "。必要列必须精确为："
            + "、".join(REQUIRED_COLUMNS)
        )


def _validate_grade_and_gpa(grade: str, gpa: Decimal | None, row_index: int) -> None:
    if grade not in ALLOWED_GRADES:
        raise ValidationError(
            f"第 {row_index} 行：等第 {grade} 不合法。允许值：" + "、".join(sorted(ALLOWED_GRADES))
        )

    if grade in EXCLUDED_GRADES:
        return

    if gpa is None:
        raise ValidationError(f"第 {row_index} 行：等第为 {grade} 时，绩点不能为空。")

    if grade in {"A+", "A"} and gpa != Decimal("4"):
        raise ValidationError(f"第 {row_index} 行：等第 {grade} 的绩点必须为 4。")
    if grade == "A-" and not (Decimal("3.7") <= gpa <= Decimal("3.8")):
        raise ValidationError(f"第 {row_index} 行：等第 A- 的绩点必须在 3.7 到 3.8。")
    if grade == "B+" and not (Decimal("3.3") <= gpa <= Decimal("3.6")):
        raise ValidationError(f"第 {row_index} 行：等第 B+ 的绩点必须在 3.3 到 3.6。")
    if grade == "B" and not (Decimal("3.0") <= gpa <= Decimal("3.2")):
        raise ValidationError(f"第 {row_index} 行：等第 B 的绩点必须在 3.0 到 3.2。")
    if grade == "B-" and not (Decimal("2.7") <= gpa <= Decimal("2.9")):
        raise ValidationError(f"第 {row_index} 行：等第 B- 的绩点必须在 2.7 到 2.9。")
    if grade == "C+" and not (Decimal("2.3") <= gpa <= Decimal("2.6")):
        raise ValidationError(f"第 {row_index} 行：等第 C+ 的绩点必须在 2.3 到 2.6。")
    if grade == "C" and not (Decimal("2.0") <= gpa <= Decimal("2.2")):
        raise ValidationError(f"第 {row_index} 行：等第 C 的绩点必须在 2.0 到 2.2。")
    if grade == "C-" and not (Decimal("1.7") <= gpa <= Decimal("1.9")):
        raise ValidationError(f"第 {row_index} 行：等第 C- 的绩点必须在 1.7 到 1.9。")
    if grade == "D" and gpa != Decimal("1.3"):
        raise ValidationError(f"第 {row_index} 行：等第 D 的绩点必须为 1.3。")
    if grade == "D-" and gpa != Decimal("1.0"):
        raise ValidationError(f"第 {row_index} 行：等第 D- 的绩点必须为 1.0。")


def _validate_semester(semester: str, row_index: int) -> None:
    if semester not in CANONICAL_SEMESTER_INDEX:
        raise ValidationError(
            f"第 {row_index} 行：修读时间 {semester} 不合法。"
            + "允许值："
            + "、".join(CANONICAL_SEMESTERS)
        )


def load_courses_from_csv_text(csv_text: str) -> list[Course]:
    dialect = detect_csv_dialect_from_text(csv_text)

    courses: list[Course] = []
    with StringIO(csv_text) as f:
        reader = csv.DictReader(f, dialect=dialect)
        _validate_header(reader.fieldnames)

        for row_num, row in enumerate(reader, start=2):
            name = normalize_text(row.get("课程名称"))
            if not name:
                continue

            semester = normalize_text(row.get("修读时间"))
            if semester == "":
                raise ValidationError(f"第 {row_num} 行：修读时间不能为空。")
            _validate_semester(semester, row_num)

            credit = parse_decimal(normalize_text(row.get("学分")), "学分", row_num)
            if credit <= 0:
                raise ValidationError(f"第 {row_num} 行：学分必须大于 0。")

            grade = normalize_text(row.get("等第")).upper()
            gpa_text = normalize_text(row.get("绩点"))
            gpa = None if gpa_text == "" else parse_decimal(gpa_text, "绩点", row_num)

            _validate_grade_and_gpa(grade, gpa, row_num)

            course_type = ""
            remark = ""
            if row.get("课程类型") is not None:
                course_type = normalize_text(row.get("课程类型"))
            if row.get("备注") is not None:
                remark = normalize_text(row.get("备注"))

            courses.append(
                Course(
                    name=name,
                    semester=semester,
                    credit=credit,
                    grade=grade,
                    gpa=gpa,
                    course_type=course_type,
                    remark=remark,
                )
            )

    if not courses:
        raise ValidationError("CSV 中没有读取到有效课程数据。")
    return courses


def load_courses_from_csv(csv_path: Path) -> list[Course]:
    if not csv_path.exists():
        raise FileNotFoundError(f"未找到 CSV 文件：{csv_path}")
    return load_courses_from_csv_bytes(csv_path.read_bytes())


def load_courses_from_csv_bytes(raw_bytes: bytes) -> list[Course]:
    csv_text = decode_csv_bytes(raw_bytes)
    return load_courses_from_csv_text(csv_text)


def get_semesters(courses: list[Course]) -> list[str]:
    unique = {c.semester for c in courses if c.semester}
    known = [s for s in CANONICAL_SEMESTERS if s in unique]
    others = sorted([s for s in unique if s not in CANONICAL_SEMESTER_INDEX])
    return known + others


def default_included(course: Course) -> bool:
    return (course.grade not in EXCLUDED_GRADES) and (course.gpa is not None)


def calculate_weighted_gpa(courses: list[Course], include_map: dict[str, bool] | None = None) -> tuple[Decimal, Decimal]:
    include_map = include_map or {}
    total_credits = Decimal("0")
    weighted_sum = Decimal("0")

    for c in courses:
        cid = f"{c.semester}::{c.name}"
        included = include_map.get(cid, default_included(c))
        if not included:
            continue
        if c.gpa is None:
            raise ValidationError(f"课程【{c.name}】没有绩点，无法计入。")

        total_credits += c.credit
        weighted_sum += c.credit * c.gpa

    if total_credits == 0:
        raise ValidationError("纳入绩点的课程总学分为 0，无法计算平均绩点。")

    return total_credits, weighted_sum / total_credits


def format_decimal(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="CSV 绩点计算")
    parser.add_argument("csv_file", type=str, help="CSV 文件路径")
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    courses = load_courses_from_csv(csv_path)
    total_credits, avg = calculate_weighted_gpa(courses)
    print(f"课程数: {len(courses)}")
    print(f"总学分: {total_credits}")
    print(f"平均绩点: {format_decimal(avg)}")


if __name__ == "__main__":
    _cli()
