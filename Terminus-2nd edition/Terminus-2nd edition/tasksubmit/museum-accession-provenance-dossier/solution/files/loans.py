from __future__ import annotations


def _dates_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return a_start <= b_end and b_start <= a_end


def detect_conflicts(loans: list[dict[str, str]], focus_id: str, as_of: str) -> list[dict[str, str]]:
    focus_loans = [loan for loan in loans if loan["accession_id"] == focus_id]
    focus_loans.sort(
        key=lambda loan: (
            loan["loan_start"],
            loan["loan_end"],
            loan["return_by"],
            loan["borrower"],
        )
    )
    out: list[dict[str, str]] = []
    for loan in focus_loans:
        if loan["return_by"] < as_of:
            out.append({"accession_id": focus_id, "reason": "missed_return_window"})
    for i, left in enumerate(focus_loans):
        for right in focus_loans[i + 1 :]:
            if _dates_overlap(left["loan_start"], left["loan_end"], right["loan_start"], right["loan_end"]):
                out.append({"accession_id": focus_id, "reason": "overlapping_loan"})
    return out
