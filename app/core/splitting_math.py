def calculate_split(assignments: list, people: list) -> tuple:
    totals = {p: 0.0 for p in people}
    unassigned = []

    for a in assignments:
        custom_split = a.get("Custom_Split")

        # If the user entered custom amounts via the Edit button
        if custom_split:
            for p, amount in custom_split.items():
                totals[p] += amount

            # If the custom amounts equal exactly 0 in total, it counts as unassigned
            if sum(custom_split.values()) == 0:
                unassigned.append(a)

        # Normal behavior: divide price by number of selected people
        else:
            person_count = len(a["Selected"])
            if person_count > 0:
                share = a["Price"] / person_count
                for p in a["Selected"]:
                    totals[p] += share
            else:
                unassigned.append(a)

    return totals, unassigned