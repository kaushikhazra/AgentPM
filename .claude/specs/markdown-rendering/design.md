# Markdown Rendering - Design

## Approach
Create a single reusable `MarkdownRenderer` atom component that accepts a markdown string and renders formatted HTML using `react-markdown` with `remark-gfm`.

## Library Choice: react-markdown + remark-gfm
- **react-markdown**: Renders markdown to React elements (no `dangerouslySetInnerHTML`), inherently XSS-safe
- **remark-gfm**: Plugin for GitHub Flavored Markdown (tables, strikethrough, task lists)
- No separate sanitizer needed — react-markdown does not allow raw HTML by default

## Component: `MarkdownRenderer`
- **Location**: `src/components/atoms/MarkdownRenderer.tsx`
- **Props**: `content: string`, `className?: string`
- **Behavior**: Renders markdown to React elements; if content is empty/null, renders nothing
- **Wrapper**: `<div className="markdown-body {className}">` for styling

## CSS Styles
- Add `.markdown-body` styles to `base.css`
- Style headings, lists, code blocks, blockquotes, tables, links
- Use CSS variables for theme compatibility (light/dark)
- Keep styles scoped under `.markdown-body` to avoid leaking

## Integration Surfaces (5 locations)

| Surface | File | Current | Change |
|---------|------|---------|--------|
| Node detail description | `NodeDetailPage.tsx:159` | `<p>{node.description}</p>` | `<MarkdownRenderer content={node.description} />` |
| Company card description | `CompaniesPage.tsx:130` | `<p className="company-description">` | `<MarkdownRenderer content={...} className="company-description" />` |
| Company modal description | `CompaniesPage.tsx:272` | `<p>{showView.description}</p>` | `<MarkdownRenderer content={...} />` |
| Project card description | `ProjectsPage.tsx:214` | `<p className="project-desc">` | `<MarkdownRenderer content={...} className="project-desc" />` |
| Project detail subtitle | `ProjectDetailPage.tsx:148` | `subtitle={project.description}` | Keep as plain text (subtitle is a header element, not a content area) |

**Decision**: ProjectDetailPage subtitle stays plain text — it's a single-line header subtitle, not a content area. Markdown rendering there would be visually awkward.

## Edge Cases
- `null` or empty string → render nothing
- Plain text without markdown → renders as paragraph (identical to current)
- Very long markdown in card views → CSS line-clamp on wrapper still truncates
