from typing import List, Tuple, Dict
from core.models import ReceiptItem


# MODIFIED: Expects a list of ReceiptItem objects
def calculate_split(assignments: List[ReceiptItem], people: List[str]) -> Tuple[Dict[str, float], List[ReceiptItem]]:
    totals = {p: 0.0 for p in people}
    unassigned = []

    for item in assignments:
        # Check if the custom_split dictionary is not empty
        if item.custom_split:
            for p, amount in item.custom_split.items():
                totals[p] += amount

            if sum(item.custom_split.values()) == 0:
                unassigned.append(item)

        # Normal behavior
        else:
            person_count = len(item.selected_people)
            if person_count > 0:
                share = item.price / person_count
                for p in item.selected_people:
                    totals[p] += share
            else:
                unassigned.append(item)

    return totals, unassigned