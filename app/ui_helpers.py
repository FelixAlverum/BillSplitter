import streamlit as st
from typing import List
from core.config import PEOPLE
from core.models import ReceiptItem

def toggle_button(key: str):
    st.session_state[key] = not st.session_state[key]


def toggle_all(item_index: int, people_list: List[str]):
    all_selected = all(st.session_state.get(f"btn_state_{item_index}_{p}", False) for p in people_list)
    new_state = not all_selected
    for p in people_list:
        st.session_state[f"btn_state_{item_index}_{p}"] = new_state


def reset_state():
    keys_to_delete = [
        key for key in st.session_state.keys()
        if key.startswith(("btn_state_", "btn_all_", "custom_split_", "loaded_"))
    ]
    for key in keys_to_delete:
        del st.session_state[key]


@st.dialog("✏️ Edit Custom Split")
def edit_item_split_dialog(item_index: int, item_name: str, item_price: float, people: List[str]):
    st.write(f"**{item_name}**")
    st.write(f"Total to split: **{item_price:.2f} €**")

    state_key = f"custom_split_{item_index}"
    current_splits = st.session_state.get(state_key, {})

    if not current_splits:
        selected = [p for p in people if st.session_state.get(f"btn_state_{item_index}_{p}", False)]
        if selected:
            share = item_price / len(selected)
            current_splits = {p: share if p in selected else 0.0 for p in people}
        else:
            current_splits = {p: 0.0 for p in people}

    new_splits = {}
    total_entered = 0.0

    for p in people:
        new_splits[p] = st.number_input(
            f"{p}'s share (€)", min_value=0.0, value=float(current_splits.get(p, 0.0)),
            step=0.50, format="%.2f"
        )
        total_entered += new_splits[p]

    st.divider()
    diff = item_price - total_entered

    if abs(diff) > 0.01:
        st.warning(f"⚠️ Total entered: {total_entered:.2f} € (Difference: {diff:+.2f} €)")
    else:
        st.success(f"✅ Exact match ({total_entered:.2f} €)")

    col1, col2 = st.columns(2)
    if col1.button("💾 Save Custom Split", type="primary", use_container_width=True):
        st.session_state[state_key] = new_splits
        st.rerun()

    if col2.button("🗑️ Reset to Default", use_container_width=True):
        if state_key in st.session_state:
            del st.session_state[state_key]
        st.rerun()


def render_items_table(items: List[ReceiptItem]) -> List[ReceiptItem]:
    """Renders the grid of items and toggle buttons, returning the assignment list."""
    assignments = []
    col_widths = [3.5, 1] + [0.5] * len(PEOPLE) + [0.6, 0.6]

    cols = st.columns(col_widths)
    cols[0].markdown("**Item**")
    cols[1].markdown("**Price**")
    st.divider()

    for i, item in enumerate(items):
        item_name = item.name
        item_price = item.price

        cols = st.columns(col_widths)
        cols[0].write(item_name)
        cols[1].write(f"{item_price:.2f} €")

        selected_persons = []
        custom_split_key = f"custom_split_{i}"
        has_custom_split = custom_split_key in st.session_state

        for j, person in enumerate(PEOPLE):
            state_key = f"btn_state_{i}_{person}"

            # Default logic for the main splitter
            if state_key not in st.session_state:
                st.session_state[state_key] = "PFAND" in item_name.upper()

            if has_custom_split:
                btn_type = "primary" if st.session_state[custom_split_key].get(person, 0) > 0 else "secondary"
            else:
                btn_type = "primary" if st.session_state[state_key] else "secondary"

            cols[j + 2].button(
                person[0], key=f"btn_ui_{i}_{person}", on_click=toggle_button,
                args=(state_key,), type=btn_type, use_container_width=True, disabled=has_custom_split
            )

            if st.session_state[state_key] and not has_custom_split:
                selected_persons.append(person)

        cols[-2].button(
            "All", key=f"btn_all_{i}", on_click=toggle_all, args=(i, PEOPLE),
            type="secondary", use_container_width=True, disabled=has_custom_split
        )

        if cols[-1].button("✏️", key=f"btn_edit_{i}", use_container_width=True):
            edit_item_split_dialog(i, item_name, item_price, PEOPLE)

        assignments.append(ReceiptItem(
            name=item_name, price=item_price, selected_people=selected_persons,
            custom_split=st.session_state.get(custom_split_key, {})
        ))

    return assignments