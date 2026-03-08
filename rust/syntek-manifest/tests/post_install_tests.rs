//! US074 — Post-install printer tests
//!
//! Acceptance criterion:
//!   Given any installer completes
//!   When post-install steps exist (URL patterns, migration commands, native build steps)
//!   Then they are printed as formatted copy-paste snippets — never written to files automatically.
//!
//! RED phase — tests will fail until the stub is replaced with real logic.

use syntek_manifest::manifest::PostInstallStep;
use syntek_manifest::post_install::PostInstallPrinter;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn make_step(label: &str, snippet: &str, lang: &str) -> PostInstallStep {
    PostInstallStep {
        label: label.to_string(),
        snippet: snippet.to_string(),
        lang: lang.to_string(),
    }
}

// ---------------------------------------------------------------------------
// render_step — single step format
// ---------------------------------------------------------------------------

#[test]
fn render_step_contains_snippet_text() {
    let step = make_step(
        "Add URL patterns",
        "path('auth/', include('syntek_auth.urls')),",
        "python",
    );

    let output = PostInstallPrinter::render_step(&step);

    assert!(
        output.contains("syntek_auth.urls"),
        "Rendered step should contain the snippet text. Got:\n{output}"
    );
}

#[test]
fn render_step_contains_label() {
    let step = make_step("Add URL patterns", "# some snippet", "python");

    let output = PostInstallPrinter::render_step(&step);

    assert!(
        output.contains("Add URL patterns"),
        "Rendered step should contain the label. Got:\n{output}"
    );
}

#[test]
fn render_step_contains_language_identifier() {
    let step = make_step("Run migration", "python manage.py migrate", "bash");

    let output = PostInstallPrinter::render_step(&step);

    assert!(
        output.contains("bash"),
        "Rendered step should include the language identifier. Got:\n{output}"
    );
}

#[test]
fn render_step_has_visible_separator_or_border() {
    let step = make_step("Add URL patterns", "path('auth/', ...)", "python");

    let output = PostInstallPrinter::render_step(&step);

    // Any separator character: ─ (U+2500), ━, -, =, or a line of dashes.
    let has_separator = output.contains('─')
        || output.contains('━')
        || output.contains("---")
        || output.contains("===")
        || output.contains("───");

    assert!(
        has_separator,
        "Rendered step should have a visible separator line. Got:\n{output}"
    );
}

// ---------------------------------------------------------------------------
// render_all — multiple steps
// ---------------------------------------------------------------------------

#[test]
fn render_all_includes_all_step_labels() {
    let steps = vec![
        make_step(
            "Add URL patterns",
            "path('auth/', include('syntek_auth.urls')),",
            "python",
        ),
        make_step("Run migrations", "python manage.py migrate", "bash"),
    ];

    let output = PostInstallPrinter::render_all(&steps);

    assert!(
        output.contains("Add URL patterns"),
        "render_all output should contain the first step label. Got:\n{output}"
    );
    assert!(
        output.contains("Run migrations"),
        "render_all output should contain the second step label. Got:\n{output}"
    );
}

#[test]
fn render_all_includes_all_snippet_texts() {
    let steps = vec![
        make_step(
            "Add URL patterns",
            "path('auth/', include('syntek_auth.urls')),",
            "python",
        ),
        make_step("Run migrations", "python manage.py migrate", "bash"),
    ];

    let output = PostInstallPrinter::render_all(&steps);

    assert!(
        output.contains("syntek_auth.urls"),
        "render_all output should contain first snippet. Got:\n{output}"
    );
    assert!(
        output.contains("python manage.py migrate"),
        "render_all output should contain second snippet. Got:\n{output}"
    );
}

#[test]
fn render_all_empty_steps_returns_empty_or_blank() {
    let output = PostInstallPrinter::render_all(&[]);
    // Either empty string or a blank/whitespace-only string is acceptable.
    assert!(
        output.trim().is_empty(),
        "render_all with no steps should produce empty output. Got:\n{output}"
    );
}

// ---------------------------------------------------------------------------
// step_header — formatted header line
// ---------------------------------------------------------------------------

#[test]
fn step_header_contains_label_text() {
    let header = PostInstallPrinter::step_header("Add URL patterns");

    assert!(
        header.contains("Add URL patterns"),
        "Header should contain the label. Got: {header}"
    );
}

#[test]
fn step_header_is_not_just_the_raw_label() {
    let label = "Add URL patterns";
    let header = PostInstallPrinter::step_header(label);

    assert_ne!(
        header.trim(),
        label,
        "Header should be formatted, not just the bare label. Got: {header}"
    );
}

// ---------------------------------------------------------------------------
// output_contains_snippet — convenience predicate
// ---------------------------------------------------------------------------

#[test]
fn output_contains_snippet_returns_true_when_snippet_is_in_rendered_output() {
    // This test will pass only when render_step() is implemented to include the snippet.
    let step = make_step("Add URL patterns", "syntek_auth.urls", "python");

    let result = PostInstallPrinter::output_contains_snippet(&step);

    assert!(
        result,
        "output_contains_snippet should return true when the rendered step contains the snippet"
    );
}

// ---------------------------------------------------------------------------
// M2 — step_header aligns correctly with wide Unicode characters
// ---------------------------------------------------------------------------

#[test]
fn step_header_aligns_correctly_with_cjk_label() {
    // The key property of the M2 fix: a single CJK character ("安") occupies
    // 2 terminal columns but counts as 1 Unicode scalar value.
    //
    // With the BROKEN implementation (chars().count()):
    //   "── 安 " has chars().count() == 5 → 59 trailing dashes
    // With the CORRECT implementation (UnicodeWidthStr::width):
    //   "── 安 " has display width 6 → 58 trailing dashes
    //
    // The ASCII equivalent that has the same NUMBER of scalar values as the
    // CJK label (i.e. same chars().count()) but DIFFERENT column width:
    //   "── X " — 5 scalars — has display width 5 → 59 trailing dashes
    //
    // We compare the CJK header against the ASCII header of the same scalar
    // count. With the correct fix the CJK header has fewer trailing dashes
    // (because the CJK char was wider in columns). With the broken approach
    // they would be equal.
    let cjk_header = PostInstallPrinter::step_header("安"); // 1 scalar, 2 columns
    let ascii_header = PostInstallPrinter::step_header("X"); // 1 scalar, 1 column

    let cjk_trailing = cjk_header.chars().filter(|&c| c == '─').count();
    let ascii_trailing = ascii_header.chars().filter(|&c| c == '─').count();

    // With unicode-width: CJK label is wider → prefix is wider → fewer trailing dashes.
    assert!(
        cjk_trailing < ascii_trailing,
        "A single CJK char occupies 2 columns; step_header should produce fewer trailing \
         dashes for a CJK label than for an ASCII label with the same scalar count.\n\
         CJK trailing dashes: {cjk_trailing} (header: {cjk_header})\n\
         ASCII trailing dashes: {ascii_trailing} (header: {ascii_header})"
    );
}

#[test]
fn step_header_aligns_correctly_with_emoji_label() {
    // A single emoji ("🚀") occupies 2 terminal columns (emoji are wide) but
    // counts as 1 Unicode scalar value.
    //
    // This mirrors the CJK test: the emoji header should have fewer trailing
    // dashes than the ASCII header of the same scalar count ("X" = 1 scalar,
    // 1 column) because the emoji consumed an extra terminal column.
    let emoji_header = PostInstallPrinter::step_header("🚀"); // 1 scalar, 2 columns
    let ascii_header = PostInstallPrinter::step_header("X"); // 1 scalar, 1 column

    let emoji_trailing = emoji_header.chars().filter(|&c| c == '─').count();
    let ascii_trailing = ascii_header.chars().filter(|&c| c == '─').count();

    assert!(
        emoji_trailing < ascii_trailing,
        "A single emoji occupies 2 terminal columns; step_header should produce fewer \
         trailing dashes for an emoji label than for an equal-length ASCII label.\n\
         Emoji trailing dashes: {emoji_trailing} (header: {emoji_header})\n\
         ASCII trailing dashes: {ascii_trailing} (header: {ascii_header})"
    );
}

// ---------------------------------------------------------------------------
// L4 — render_all produces a single blank line between steps (not double)
// ---------------------------------------------------------------------------

#[test]
fn render_all_has_single_blank_line_between_steps() {
    let steps = vec![
        make_step("Step one", "snippet one", "python"),
        make_step("Step two", "snippet two", "bash"),
    ];

    let output = PostInstallPrinter::render_all(&steps);

    // A double blank line would appear as "\n\n\n" (footer \n + join "\n" + header).
    // We verify that "\n\n\n" (triple newline = double blank line) is not present.
    assert!(
        !output.contains("\n\n\n"),
        "render_all should not produce double blank lines between steps. Got:\n{output}"
    );

    // Verify both steps are present.
    assert!(output.contains("Step one"), "First step label present");
    assert!(output.contains("Step two"), "Second step label present");
}

// ---------------------------------------------------------------------------
// MC3 — print_all writes to stdout, never to files
// ---------------------------------------------------------------------------

#[test]
fn print_all_does_not_panic_on_empty_steps() {
    // We cannot easily capture stdout in a unit test without external crates.
    // This test verifies that print_all does not panic or error when given an
    // empty slice — the function should silently no-op.
    PostInstallPrinter::print_all(&[]);
}

#[test]
fn print_all_does_not_panic_on_valid_steps() {
    let steps = vec![make_step(
        "Add URL patterns",
        "path('auth/', include('syntek_auth.urls')),",
        "python",
    )];
    // Verifies that print_all runs without panicking. Stdout capture would require
    // a dependency on `gag` or process-level redirection — out of scope for unit tests.
    PostInstallPrinter::print_all(&steps);
}

#[test]
fn render_all_output_matches_concatenated_render_step_calls() {
    // MC3: render_all is the source of truth for print_all. Verify that the
    // string returned by render_all equals manually concatenated render_step calls.
    let steps = vec![
        make_step("Step one", "snippet one", "python"),
        make_step("Step two", "snippet two", "bash"),
    ];

    let from_render_all = PostInstallPrinter::render_all(&steps);
    let manual = steps
        .iter()
        .map(PostInstallPrinter::render_step)
        .collect::<String>();

    assert_eq!(
        from_render_all, manual,
        "render_all should produce the same output as concatenated render_step calls"
    );
}
