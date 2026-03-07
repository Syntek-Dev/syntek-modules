use colored::Colorize;

pub fn header(title: &str) {
    println!();
    println!("{}", "===========================================".dimmed());
    println!("  {}", title.bold().green());
    println!("{}", "===========================================".dimmed());
}

pub fn section(title: &str) {
    println!();
    println!("{}", title.bold().blue());
    println!("{}", "-------------------------------------------".dimmed());
}

pub fn step(msg: &str) {
    println!("  {} {}", "-->".cyan(), msg);
}

pub fn ok(msg: &str) {
    println!("  {} {}", "OK".bold().green(), msg);
}

pub fn warn(msg: &str) {
    println!("  {} {}", "!".bold().yellow(), msg);
}

#[allow(dead_code)]
pub fn error(msg: &str) {
    eprintln!("  {} {}", "FAIL".bold().red(), msg);
}

pub fn summary_pass() {
    println!();
    println!("{}", "===========================================".dimmed());
    println!("  {}", "All checks passed".bold().green());
    println!("{}", "===========================================".dimmed());
}

pub fn summary_fail(count: u32) {
    println!();
    println!("{}", "===========================================".dimmed());
    println!("  {} {} layer(s) failed", "FAILED:".bold().red(), count);
    println!("{}", "===========================================".dimmed());
}
