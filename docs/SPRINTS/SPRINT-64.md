# Sprint 64 — Maps UI

**Sprint Goal**: Implement the maps, routing, and live tracking UI package — map renderer,
LocationPicker, RouteMap, LiveTracker, and driving direction components wired to the geo, routing,
and tracking backend modules.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Could 100% **Status**: Planned

## Stories

| Story                        | Title                                                | Points | MoSCoW | Dependencies Met                            |
| ---------------------------- | ---------------------------------------------------- | ------ | ------ | ------------------------------------------- |
| [US071](../STORIES/US071.md) | `@syntek/ui-maps` — Maps, Routing & Live Tracking UI | 13     | Could  | US042 ✓, US044 ✓, US065 ✓, US115 ✓, US116 ✓ |

## Notes

- US071 is a single cohesive story — map rendering, LocationPicker, RouteMap, and LiveTracker share
  a unified map context and cannot be split cleanly.
- US071 was previously grouped with US069 and US070 in Sprint 40. It has been moved here to allow
  Sprint 40 to expand the comments and feedback UI stories properly.
- Map API keys (Mapbox or Google Maps) must come from server-side GraphQL configuration — they must
  never be exposed in client bundles or environment variables.
- LiveTracker requires US116 (`syntek-tracking`) to be complete — real-time position updates are
  delivered via GraphQL subscriptions backed by Django Channels.
- RouteMap requires US115 (`syntek-routing`) — route waypoints are fetched from the route
  optimisation backend, not recalculated client-side.
