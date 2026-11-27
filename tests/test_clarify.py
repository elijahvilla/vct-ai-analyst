from analyst.clarify import clarify_options


def test_vague_best_map_asks_for_measure():
    assert clarify_options("What is the best map for Chamber?") == [
        "What is the best map for Chamber? (by most picks)",
        "What is the best map for Chamber? (by highest win rate, at least 20 picks)",
    ]


def test_vague_best_player_offers_player_measures():
    opts = clarify_options("Who is the best Jett player in 2025?")
    assert opts == ["Who is the best Jett player in 2025? (by highest average rating)",
                    "Who is the best Jett player in 2025? (by most kills)"]


def test_clear_questions_are_not_ambiguous():
    for q in ["Which agent had the highest win rate on Lotus?", "Who had the most kills on Jett in 2025?",
              "Which 5 agents had the highest pick rate at Valorant Champions 2024?", "How many maps were played in 2024?"]:
        assert clarify_options(q) is None, q


def test_already_clarified_question_is_not_ambiguous():
    assert clarify_options("What is the best map for Chamber? (by most picks)") is None
