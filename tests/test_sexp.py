import pytest

from pufdfm.sexp import Str, find, find_all, parse, prop


def test_nested_lists_atoms_and_numbers_stay_text():
    t = parse("(a (b 1 2.5) (c x))")
    assert t == ["a", ["b", "1", "2.5"], ["c", "x"]]


def test_quoted_strings_keep_spaces_and_escaped_quotes_and_are_marked_as_strings():
    t = parse('(property "Value" "say \\"hi\\" now")')
    assert t[2] == 'say "hi" now' and isinstance(t[2], Str) and not isinstance(t[0], Str)


def test_a_quoted_string_and_a_bare_atom_with_the_same_text_are_distinguishable():
    t = parse('(x yes "yes")')
    assert not isinstance(t[1], Str) and isinstance(t[2], Str)


def test_tabs_windows_line_ends_and_blank_lines_are_whitespace():
    assert parse("(a\r\n\t(b 1)\r\n\r\n)") == ["a", ["b", "1"]]


def test_unbalanced_input_is_rejected():
    with pytest.raises(ValueError):
        parse("(a (b 1)")


def test_find_find_all_and_prop():
    t = parse('(s (property "Reference" "R1") (property "Value" "10k") (dnp yes) (dnp no))')
    assert prop(t, "Value") == "10k" and prop(t, "Missing") is None
    assert find(t, "dnp") == ["dnp", "yes"] and len(find_all(t, "dnp")) == 2 and find(t, "nope", "d") == "d"
