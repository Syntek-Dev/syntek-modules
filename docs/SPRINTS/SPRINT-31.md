# Sprint 31 — Web Design System (@syntek/ui)

**Sprint Goal**: Implement the complete Syntek web design system — all primitive, composite, and
layout components; form elements; navigation; overlays; data display; and rich text — token-driven
and fully accessible.

**Total Points**: 21 / 11 ⚠️⚠️ SIGNIFICANTLY OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**:
Planned

## Stories

| Story                        | Title                            | Points | MoSCoW | Dependencies Met |
| ---------------------------- | -------------------------------- | ------ | ------ | ---------------- |
| [US042](../STORIES/US042.md) | `@syntek/ui` — Web Design System | 21     | Must   | US003 ✓, US001 ✓ |

## Notes

- ⚠️⚠️ This story is 21 points — nearly double sprint capacity. Strongly recommended to split at
  sprint kick-off into three sub-sprints:
  - **ui-primitives** (~8pts): Button, Input, Textarea, Select, Checkbox, Radio, Toggle, Label,
    Badge, Avatar, Icon slots
  - **ui-composite** (~8pts): Modal, Drawer, Tooltip, Popover, DropdownMenu, ContextMenu, Accordion,
    Tabs, DatePicker, TimePicker, Slider, FileUpload, RichTextEditor
  - **ui-layout** (~5pts): Header, Navbar, Footer, Breadcrumbs, Pagination, Stepper, Hero, Section,
    Container, Grid, Stack, Cluster
- **Parallel opportunity**: This sprint can start from Sprint 3 onwards (only needs US001 and US003
  which complete in Sprint 2). Frontend work can run entirely in parallel with the Rust and backend
  streams.
- All components must consume design tokens from US003 — no hardcoded colours, spacing, or
  typography.
- Icon slots are React nodes — Font Awesome Pro is recommended but any package works.
- All components must meet WCAG 2.2 AA accessibility standards.
