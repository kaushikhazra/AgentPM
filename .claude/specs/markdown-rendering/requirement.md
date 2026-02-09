# Markdown Rendering - Requirements

## Overview
Node descriptions in Taskyn support markdown but are currently displayed as raw text. Implement proper markdown rendering so formatting is visually rendered in the Web UI.

## User Stories

### US-1: View formatted node descriptions
**As a** project manager,
**I want** node descriptions rendered with markdown formatting (bold, lists, headings, links, code blocks),
**So that** I can write rich, structured descriptions and see them properly displayed.

### US-2: Consistent rendering across all surfaces
**As a** user browsing projects and nodes,
**I want** markdown rendering to work everywhere descriptions appear (detail pages, cards, modals),
**So that** the experience is consistent regardless of where I view a description.

### US-3: Safe rendering
**As a** user,
**I want** markdown rendering to be safe from XSS attacks,
**So that** malicious content in descriptions cannot execute scripts.

### US-4: Theme-aware styling
**As a** user,
**I want** rendered markdown to respect the current theme (light/dark mode),
**So that** code blocks, links, and other elements look correct in both themes.

## Acceptance Criteria
- All markdown formatting renders correctly: headings, bold, italic, lists, links, code blocks, blockquotes, tables
- GFM (GitHub Flavored Markdown) is supported (task lists, strikethrough, tables)
- XSS-safe — no raw HTML injection
- Works in both light and dark themes
- Description cards with line-clamp still truncate gracefully
- Plain text without markdown renders identically to current behavior
