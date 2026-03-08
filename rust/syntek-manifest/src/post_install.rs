//! Post-install step printer.
//!
//! Formats `post_install_steps[]` from the manifest as copy-paste snippets.
//! Steps are printed to stdout — they are never written to files automatically.
//!
//! Each step is rendered as:
//!
//! ```text
//! ── Add URL patterns ─────────────────────────────────────────────
//! # python
//! path('auth/', include('syntek_auth.urls')),
//! ─────────────────────────────────────────────────────────────────
//! ```

use unicode_width::UnicodeWidthStr;

use crate::manifest::PostInstallStep;

/// Total width of the separator line in terminal columns.
const SEPARATOR_WIDTH: usize = 64;

/// The separator character (Unicode box-drawing horizontal line).
const SEP_CHAR: char = '─';

/// Formats post-install steps for developer output.
pub struct PostInstallPrinter;

impl PostInstallPrinter {
    /// Render a single post-install step as a formatted snippet string.
    ///
    /// The output includes a labelled header line, a language comment,
    /// the snippet text, and a closing separator line.
    ///
    /// # Parameters
    /// - `step` — the post-install step to render
    ///
    /// # Returns
    /// A formatted multi-line string suitable for printing to stdout.
    pub fn render_step(step: &PostInstallStep) -> String {
        let header = Self::step_header(&step.label);
        let footer = SEP_CHAR.to_string().repeat(SEPARATOR_WIDTH);
        format!(
            "{header}\n# {lang}\n{snippet}\n{footer}\n",
            lang = step.lang,
            snippet = step.snippet,
        )
    }

    /// Render all post-install steps in order and return as a single string.
    ///
    /// An empty slice produces an empty string.
    ///
    /// L4: steps are joined with `""` (empty string) rather than `"\n"`.
    /// `render_step` already appends a trailing `\n` after the footer, so
    /// joining with `"\n"` would produce a double blank line between steps,
    /// making the between-step gap inconsistent with the within-step spacing.
    ///
    /// # Parameters
    /// - `steps` — the slice of post-install steps from the manifest
    ///
    /// # Returns
    /// A concatenated string of all rendered steps.
    pub fn render_all(steps: &[PostInstallStep]) -> String {
        steps
            .iter()
            .map(Self::render_step)
            .collect::<Vec<_>>()
            .join("")
    }

    /// Print all post-install steps to stdout.
    ///
    /// MC3: this is the only entry point for writing step output. Steps are
    /// never written to the filesystem automatically; this function uses
    /// `println!` which targets stdout exclusively.
    ///
    /// # Parameters
    /// - `steps` — the slice of post-install steps from the manifest
    pub fn print_all(steps: &[PostInstallStep]) {
        let output = Self::render_all(steps);
        if !output.is_empty() {
            println!("{output}");
        }
    }

    /// Return the header line for a step label.
    ///
    /// The label is embedded in a line of `─` characters padded to
    /// [`SEPARATOR_WIDTH`] total terminal columns.
    ///
    /// M2: uses [`UnicodeWidthStr::width`] rather than `.chars().count()` to
    /// measure the display width of the prefix string. CJK characters and emoji
    /// each occupy two terminal columns but count as one scalar value; using
    /// `chars().count()` would produce a header that is too short in those cases.
    ///
    /// # Parameters
    /// - `label` — the human-readable step label
    ///
    /// # Returns
    /// A formatted header string, e.g. `"── Add URL patterns ────────────────────────────────────"`.
    pub fn step_header(label: &str) -> String {
        // Format: "── <label> " followed by trailing dashes to reach SEPARATOR_WIDTH.
        let prefix = format!("── {label} ");
        // M2: measure display columns, not Unicode scalar count.
        let prefix_width = UnicodeWidthStr::width(prefix.as_str());
        let remaining = SEPARATOR_WIDTH.saturating_sub(prefix_width);
        let trailing = SEP_CHAR.to_string().repeat(remaining);
        format!("{prefix}{trailing}")
    }

    /// Return `true` if the rendered output for a step contains the snippet text.
    ///
    /// Convenience predicate used in tests to verify that [`render_step`]
    /// includes the raw snippet without transformation.
    ///
    /// # Parameters
    /// - `step` — the post-install step to check
    ///
    /// # Returns
    /// `true` when the rendered step output contains `step.snippet`.
    pub fn output_contains_snippet(step: &PostInstallStep) -> bool {
        Self::render_step(step).contains(&step.snippet)
    }
}
