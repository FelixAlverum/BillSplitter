def calculate_split(assignments: list, people: list) -> tuple:
    """
    Takes assignments and returns how much each person owes,
    and a list of unassigned items.
    """
    totals = {p: 0.0 for p in people}
    unassigned = []

    for a in assignments:
        person_count = len(a["Selected"])
        if person_count > 0:
            share = a["Price"] / person_count
            for p in a["Selected"]:
                totals[p] += share
        else:
            unassigned.append(a)

    return totals, unassigned