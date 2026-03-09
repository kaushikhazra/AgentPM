# Learning Methodology — Tasks

## 1. Backend: Methodology Class & Registration

- [x] Velasari creates `LearningMethodology` class in `src/taskyn/methodologies/learning.py` with subject, topic, and activity node types — _LM-1, LM-2, LM-3, LM-4_
  - [x] Subject: planned→active→completed→archived, can_track_time=False
  - [x] Topic: planned→researching→practicing→documenting→completed→archived (non-gated), can_track_time=False
  - [x] Activity: todo→in_progress→done→cancelled, can_track_time=True
- [x] Velasari defines edge types (parent, depends_on, relates_to) in `LearningMethodology.edge_types` — _LM-7_
- [x] Velasari defines `valid_parent_pairs` enforcing subject→topic→activity hierarchy in `LearningMethodology` — _LM-5_
- [x] Velasari overrides helper methods (get_story_type, get_task_type, get_in_progress_status, get_done_status, get_blocked_status) in `LearningMethodology` — _LM-9_
- [x] Velasari adds `LEARNING = "learning"` to `Methodology` enum in `src/taskyn/db/enums.py` — _LM-1_
- [x] Velasari imports and registers `LearningMethodology` in `src/taskyn/methodologies/__init__.py` — _LM-1_
- [x] Velasari writes unit tests in `tests/test_learning_methodology.py` covering registration, node types, transitions, edge validation, hierarchy, and helpers — _LM-1 through LM-9_

## 2. Frontend: UI Config & Documentation

- [x] Velasari adds `learning` entry to `METHODOLOGY_HIERARCHY` in `src/taskyn/web/frontend/src/config/methodology-ui.ts` — _LM-8_
- [x] Velasari adds `learning` entry to `METHODOLOGY_UI` in `src/taskyn/web/frontend/src/config/methodology-ui.ts` — _LM-8_
- [x] Velasari adds "Learning" option to methodology `<select>` in `src/taskyn/web/frontend/src/pages/ProjectsPage.tsx` — _LM-8_
- [x] Velasari updates Methodologies section in `CLAUDE.md` to document `learning` methodology — _LM-1_
