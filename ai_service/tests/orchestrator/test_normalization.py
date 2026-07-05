"""Unit tests for the normalize() function.

Verifies that normalize() correctly:
  - lowercases
  - strips typographic apostrophes (', ')
  - removes NFKD combining characters (accent stripping)
  - collapses multiple spaces
  - preserves hyphens
"""


from app.orchestrator.normalization import normalize


class TestNormalizeLowercaseAndStrip:
    def test_lowercases_ascii(self) -> None:
        assert normalize("BONJOUR") == "bonjour"

    def test_strips_leading_trailing_spaces(self) -> None:
        assert normalize("  prix  ") == "prix"

    def test_collapses_multiple_spaces(self) -> None:
        assert normalize("mon   magasin") == "mon magasin"

    def test_empty_string(self) -> None:
        assert normalize("") == ""

    def test_only_spaces(self) -> None:
        assert normalize("   ") == ""


class TestNormalizeApostrophes:
    def test_typographic_right_single_quotation_mark(self) -> None:
        # U+2019 RIGHT SINGLE QUOTATION MARK
        assert normalize("qu’est-ce") == "qu'est-ce"

    def test_typographic_left_single_quotation_mark(self) -> None:
        # U+2018 LEFT SINGLE QUOTATION MARK
        assert normalize("l‘application") == "l'application"

    def test_backtick_apostrophe(self) -> None:
        assert normalize("l`application") == "l'application"

    def test_straight_apostrophe_unchanged(self) -> None:
        assert normalize("l'application") == "l'application"


class TestNormalizeAccents:
    def test_e_acute_removed(self) -> None:
        assert normalize("évaluer") == "evaluer"

    def test_e_grave_removed(self) -> None:
        assert normalize("où") == "ou"

    def test_c_cedilla_removed(self) -> None:
        assert normalize("garçon") == "garcon"

    def test_mixed_accents(self) -> None:
        assert normalize("Résumé") == "resume"

    def test_french_sentence_normalized(self) -> None:
        result = normalize("Quels sont les différents rôles ?")
        assert result == "quels sont les differents roles ?"

    def test_accent_on_uppercase_removed(self) -> None:
        assert normalize("ÉVALUER") == "evaluer"


class TestNormalizeHyphens:
    def test_hyphens_preserved(self) -> None:
        assert normalize("peux-tu") == "peux-tu"

    def test_hyphenated_compound_preserved(self) -> None:
        assert normalize("peut-il approuver") == "peut-il approuver"


class TestNormalizeCombined:
    def test_full_french_question(self) -> None:
        result = normalize("Pourquoi je ne peux pas voir ce magasin ?")
        assert result == "pourquoi je ne peux pas voir ce magasin ?"

    def test_promotion_question_with_accents(self) -> None:
        result = normalize("comment gérer une promotion qui ne fonctionne pas ?")
        assert result == "comment gerer une promotion qui ne fonctionne pas ?"

    def test_typographic_apostrophe_in_sentence(self) -> None:
        result = normalize("qu’est-ce que le chatbot peut faire")
        assert result == "qu'est-ce que le chatbot peut faire"

    def test_multiple_spaces_collapsed_to_one(self) -> None:
        result = normalize("prix   magasin   france")
        assert result == "prix magasin france"
