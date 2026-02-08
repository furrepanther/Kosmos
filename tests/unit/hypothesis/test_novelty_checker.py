"""Tests for novelty_checker module."""

import pytest
from unittest.mock import Mock, patch
from kosmos.hypothesis.novelty_checker import NoveltyChecker
from kosmos.models.hypothesis import Hypothesis

@pytest.fixture
def novelty_checker():
    return NoveltyChecker(similarity_threshold=0.75, use_vector_db=False)

@pytest.fixture
def sample_hypothesis():
    return Hypothesis(
        research_question="Test question",
        statement="Attention mechanism improves transformer performance",
        rationale="Prior work shows attention captures dependencies",
        domain="machine_learning"
    )

@pytest.mark.unit
class TestNoveltyChecker:
    def test_init(self, novelty_checker):
        assert novelty_checker.similarity_threshold == 0.75

    @patch('kosmos.hypothesis.novelty_checker.UnifiedLiteratureSearch')
    @patch('kosmos.hypothesis.novelty_checker.get_session')
    def test_check_novelty_high(self, mock_session, mock_search, novelty_checker, sample_hypothesis):
        mock_search_inst = Mock()
        mock_search_inst.search.return_value = []
        mock_search.return_value = mock_search_inst

        mock_sess = Mock()
        mock_sess.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_sess

        report = novelty_checker.check_novelty(sample_hypothesis)

        assert report.novelty_score >= 0.8
        assert report.is_novel is True
        assert len(report.similar_papers) == 0

    def test_keyword_similarity(self, novelty_checker):
        text1 = "attention mechanism transformer neural network"
        text2 = "transformer attention model deep learning"
        similarity = novelty_checker._keyword_similarity(text1, text2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0  # Some overlap exists


@pytest.mark.unit
class TestPaperIndexing:
    """Test that papers from keyword fallback are indexed into vector DB (D3 fix)."""

    @patch('kosmos.hypothesis.novelty_checker.UnifiedLiteratureSearch')
    def test_keyword_fallback_indexes_papers(self, mock_search):
        """Papers from keyword fallback should be indexed into vector DB."""
        from kosmos.literature.base_client import PaperMetadata, PaperSource

        mock_papers = [
            PaperMetadata(
                id="paper-1",
                source=PaperSource.SEMANTIC_SCHOLAR,
                title="Paper 1",
                authors=[],
                abstract="Abstract about transformers",
            ),
            PaperMetadata(
                id="paper-2",
                source=PaperSource.SEMANTIC_SCHOLAR,
                title="Paper 2",
                authors=[],
                abstract="Abstract about attention",
            ),
        ]

        mock_search_inst = Mock()
        mock_search_inst.search.return_value = mock_papers
        mock_search.return_value = mock_search_inst

        mock_vdb_inst = Mock()

        # use_vector_db=False so embedder is None (skips vector search path)
        # then manually set vector_db so indexing still works
        checker = NoveltyChecker(use_vector_db=False)
        checker.vector_db = mock_vdb_inst

        hypothesis = Hypothesis(
            research_question="Test question",
            statement="Transformers use attention mechanisms",
            rationale="Based on Vaswani et al. attention is all you need",
            domain="machine_learning",
        )

        papers = checker._search_similar_literature(hypothesis)

        assert len(papers) == 2
        # Verify add_papers was called with the retrieved papers
        mock_vdb_inst.add_papers.assert_called_once_with(mock_papers)

    @patch('kosmos.hypothesis.novelty_checker.UnifiedLiteratureSearch')
    def test_keyword_fallback_no_vector_db_skips_indexing(self, mock_search):
        """When vector DB is not available, indexing should be skipped."""
        from kosmos.literature.base_client import PaperMetadata, PaperSource

        mock_papers = [
            PaperMetadata(
                id="paper-1",
                source=PaperSource.SEMANTIC_SCHOLAR,
                title="Paper 1",
                authors=[],
                abstract="Abstract",
            ),
        ]

        mock_search_inst = Mock()
        mock_search_inst.search.return_value = mock_papers
        mock_search.return_value = mock_search_inst

        checker = NoveltyChecker(use_vector_db=False)

        hypothesis = Hypothesis(
            research_question="Test question",
            statement="Some hypothesis",
            rationale="Some rationale about the world and how it works",
            domain="biology",
        )

        papers = checker._search_similar_literature(hypothesis)

        assert len(papers) == 1
        # vector_db is None, so add_papers should not be called
        assert checker.vector_db is None

    @patch('kosmos.hypothesis.novelty_checker.UnifiedLiteratureSearch')
    def test_indexing_error_does_not_crash(self, mock_search):
        """If indexing fails, it should log warning but not crash."""
        from kosmos.literature.base_client import PaperMetadata, PaperSource

        mock_papers = [
            PaperMetadata(id="paper-1", source=PaperSource.SEMANTIC_SCHOLAR, title="Paper 1", authors=[], abstract="Abs"),
        ]

        mock_search_inst = Mock()
        mock_search_inst.search.return_value = mock_papers
        mock_search.return_value = mock_search_inst

        mock_vdb_inst = Mock()
        mock_vdb_inst.add_papers.side_effect = RuntimeError("ChromaDB error")

        # use_vector_db=False so we go through keyword path, then set vector_db manually
        checker = NoveltyChecker(use_vector_db=False)
        checker.vector_db = mock_vdb_inst

        hypothesis = Hypothesis(
            research_question="Test question",
            statement="Some hypothesis statement here",
            rationale="Rationale for the hypothesis being tested",
            domain="chemistry",
        )

        # Should not raise despite indexing failure
        papers = checker._search_similar_literature(hypothesis)
        assert len(papers) == 1
