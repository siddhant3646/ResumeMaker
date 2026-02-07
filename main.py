#!/usr/bin/env python3
"""
Resume Tailor CLI

A CLI tool that scrapes job descriptions, uses AI to tailor
resume bullet points, and generates ATS-friendly PDFs.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from scraper import scrape_job_description, extract_company_name, ScrapingError
from ai_agent import tailor_resume, validate_master_resume, TailoredResume
from renderer import render_and_save_pdf, preview_html

# Load environment variables from .env file
load_dotenv()


# Initialize Typer app
app = typer.Typer(
    name="resume-tailor",
    help="Tailor your resume for specific job descriptions using AI.",
    add_completion=False,
)

console = Console()

# Default path for master resume
DEFAULT_RESUME_PATH = Path(__file__).parent / "master_resume.json"


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Limit length
    return sanitized[:50]


def load_master_resume(path: Path) -> dict:
    """Load and validate the master resume JSON file."""
    if not path.exists():
        rprint(f"[bold red]Error:[/bold red] Resume file not found: {path}")
        rprint("\n[yellow]Please create a master_resume.json file with your resume data.[/yellow]")
        raise typer.Exit(code=1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        rprint(f"[bold red]Error:[/bold red] Invalid JSON in resume file: {e}")
        raise typer.Exit(code=1)
    
    # Validate structure
    try:
        validate_master_resume(data)
    except ValueError as e:
        rprint(f"[bold red]Error:[/bold red] Invalid resume structure: {e}")
        raise typer.Exit(code=1)
    
    return data


def get_api_key(provided_key: Optional[str]) -> str:
    """Get API key from argument, .env file, or environment variable."""
    if provided_key:
        return provided_key
    
    env_key = os.environ.get('GOOGLE_API_KEY')
    if env_key:
        return env_key
    
    rprint("[bold red]Error:[/bold red] No API key provided.")
    rprint("\nProvide it via:")
    rprint("  • .env file with GOOGLE_API_KEY=your_key")
    rprint("  • --api-key option")
    rprint("  • GOOGLE_API_KEY environment variable")
    raise typer.Exit(code=1)


@app.command()
def apply(
    url: str = typer.Argument(
        ...,
        help="URL of the job posting (use 'manual' if providing JD via file)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key", "-k",
        help="Google API key (or set GOOGLE_API_KEY env var)",
        envvar="GOOGLE_API_KEY"
    ),
    resume_path: Path = typer.Option(
        DEFAULT_RESUME_PATH,
        "--resume", "-r",
        help="Path to master resume JSON file"
    ),
    output_dir: Path = typer.Option(
        Path("."),
        "--output", "-o",
        help="Output directory for the generated PDF"
    ),
    company_name: Optional[str] = typer.Option(
        None,
        "--company", "-c",
        help="Company name (extracted automatically if not provided)"
    ),
    model: str = typer.Option(
        "AI's Supermind",
        "--model", "-m",
        help="Google AI model to use"
    ),
    save_html: bool = typer.Option(
        False,
        "--html",
        help="Also save the HTML preview"
    ),
    jd_file: Optional[Path] = typer.Option(
        None,
        "--jd-file", "-j",
        help="Read job description from a text file (skips URL scraping)"
    ),
):
    """
    Tailor your resume for a specific job posting.
    
    Scrapes the job description from the URL (or prompts for manual input),
    uses AI to rewrite bullet points, and generates an ATS-friendly PDF.
    
    Example:
        python main.py apply "https://example.com/job/123" --api-key YOUR_KEY
    """
    console.print(Panel.fit(
        "[bold blue]Resume Tailor[/bold blue] - AI-Powered Resume Customization",
        border_style="blue"
    ))
    
    # Get API key
    api_key_value = get_api_key(api_key)
    
    # Load master resume
    rprint(f"\n[cyan]Loading resume from:[/cyan] {resume_path}")
    master_resume = load_master_resume(resume_path)
    rprint("[green]✓[/green] Resume loaded successfully")
    
    # Get job description from file or URL
    job_description = None
    extracted_company = None
    
    # Option 1: Read from file if provided
    if jd_file:
        if not jd_file.exists():
            rprint(f"[bold red]Error:[/bold red] JD file not found: {jd_file}")
            raise typer.Exit(code=1)
        
        rprint(f"\n[cyan]Reading job description from:[/cyan] {jd_file}")
        with open(jd_file, 'r', encoding='utf-8') as f:
            job_description = f.read().strip()
        
        if len(job_description) < 50:
            rprint("[bold red]Error:[/bold red] Job description file is too short.")
            raise typer.Exit(code=1)
        
        rprint(f"[green]✓[/green] Job description loaded ({len(job_description)} characters)")
    
    # Option 2: Scrape from URL
    elif url.lower() != 'manual':
        rprint(f"\n[cyan]Scraping job description from:[/cyan] {url}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Fetching page...", total=None)
                job_description = scrape_job_description(url)
            
            rprint("[green]✓[/green] Job description scraped successfully")
            rprint(f"[dim]  ({len(job_description)} characters extracted)[/dim]")
            
            # Try to extract company name
            if not company_name:
                extracted_company = extract_company_name(job_description)
                if extracted_company:
                    rprint(f"[dim]  Detected company: {extracted_company}[/dim]")
        
        except ScrapingError as e:
            rprint(f"\n[yellow]⚠ Scraping failed:[/yellow] {e}")
            rprint("\n[bold]Please paste the job description below.[/bold]")
            rprint("[dim](Type 'END' on a new line when done, or press Ctrl+D)[/dim]\n")
            
            # Interactive fallback - collect multi-line input
            lines = []
            try:
                while True:
                    line = input()
                    # Check for END marker (case-insensitive)
                    if line.strip().upper() == 'END':
                        break
                    lines.append(line)
            except EOFError:
                pass
            
            job_description = "\n".join(lines).strip()
            
            if not job_description or len(job_description) < 50:
                rprint("[bold red]Error:[/bold red] Job description is too short or empty.")
                raise typer.Exit(code=1)
            
            rprint(f"\n[green]✓[/green] Job description received ({len(job_description)} characters)")
    
    # Ask for company name if not provided and not extracted
    final_company = company_name or extracted_company
    if not final_company:
        final_company = typer.prompt(
            "Company name (for filename)",
            default="Company"
        )
    
    # Ensure we have a job description
    if not job_description:
        rprint("[bold red]Error:[/bold red] No job description provided.")
        rprint("\n[yellow]Please provide a job description via:[/yellow]")
        rprint("  • --jd-file option")
        rprint("  • Job URL (not 'manual')")
        raise typer.Exit(code=1)
    
    # Tailor the resume using AI
    rprint(f"\n[cyan]Tailoring resume using {model}...[/cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("AI is analyzing and rewriting...", total=None)
            tailored_resume = tailor_resume(
                master_resume=master_resume,
                job_description=job_description,
                api_key=api_key_value,
                model=model
            )
        
        rprint("[green]✓[/green] Resume tailored successfully")
    
    except Exception as e:
        rprint(f"\n[bold red]Error during AI processing:[/bold red] {e}")
        rprint("\n[yellow]Possible causes:[/yellow]")
        rprint("  • Invalid API key")
        rprint("  • API quota exceeded")
        rprint("  • Network issues")
        raise typer.Exit(code=1)
    
    # Generate filename using new format: FirstNameLastNameResumeYear.pdf
    from renderer import generate_filename
    filename = generate_filename(tailored_resume.basics.name)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate PDF with page check
    pdf_path = output_dir / filename
    rprint(f"\n[cyan]Generating PDF...[/cyan]")
    rprint(f"[dim]Target filename: {filename}[/dim]")
    
    try:
        # Use the new function that ensures 1-page output
        final_pdf_path = render_and_save_pdf(tailored_resume, str(pdf_path), ensure_single_page=True)
        
        # Check final page count
        from renderer import get_pdf_page_count
        final_pages = get_pdf_page_count(final_pdf_path)
        
        if final_pages == 1:
            rprint(f"[green]✓[/green] PDF saved: [bold]{final_pdf_path}[/bold] (1 page)")
        else:
            rprint(f"[yellow]⚠[/yellow] PDF saved: [bold]{final_pdf_path}[/bold] ({final_pages} pages - best effort)")
    except Exception as e:
        rprint(f"\n[bold red]Error generating PDF:[/bold red] {e}")
        rprint("\n[yellow]If you see font errors, ensure the Times font is available.[/yellow]")
        raise typer.Exit(code=1)
    
    # Optionally save HTML
    if save_html:
        html_filename = filename.replace('.pdf', '.html')
        html_path = output_dir / html_filename
        final_html_path = preview_html(tailored_resume, str(html_path))
        rprint(f"[green]✓[/green] HTML saved: [bold]{final_html_path}[/bold]")
    
    # Success summary
    rprint("\n" + "─" * 50)
    rprint(Panel.fit(
        f"[bold green]✓ Resume tailored successfully![/bold green]\n\n"
        f"[cyan]Company:[/cyan] {final_company}\n"
        f"[cyan]Filename:[/cyan] {filename}\n"
        f"[cyan]Pages:[/cyan] {final_pages if 'final_pages' in locals() else '1'}",
        title="Complete",
        border_style="green"
    ))


@app.command()
def validate(
    resume_path: Path = typer.Argument(
        DEFAULT_RESUME_PATH,
        help="Path to the resume JSON file to validate"
    )
):
    """
    Validate a master resume JSON file.
    
    Checks that the file exists, is valid JSON, and matches the expected schema.
    """
    rprint(f"[cyan]Validating:[/cyan] {resume_path}")
    
    try:
        data = load_master_resume(resume_path)
        rprint("\n[bold green]✓ Resume is valid![/bold green]")
        rprint(f"\n[dim]Contents:[/dim]")
        rprint(f"  • Name: {data['basics']['name']}")
        rprint(f"  • Experience entries: {len(data['experience'])}")
        rprint(f"  • Education entries: {len(data['education'])}")
        rprint(f"  • Skills: {len(data['skills'])}")
        rprint(f"  • Projects: {len(data['projects'])}")
        rprint(f"  • Achievements: {len(data['achievements'])}")
    except typer.Exit:
        raise


@app.command()
def init():
    """
    Create a sample master_resume.json template.
    
    Generates a template file that you can fill in with your actual information.
    """
    output_path = Path("master_resume.json")
    
    if output_path.exists():
        overwrite = typer.confirm(
            f"{output_path} already exists. Overwrite?",
            default=False
        )
        if not overwrite:
            rprint("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()
    
    sample_resume = {
        "basics": {
            "name": "Your Name",
            "email": "your.email@example.com",
            "phone": "+1-234-567-8900",
            "location": "City, State",
            "links": [
                "https://linkedin.com/in/yourprofile",
                "https://github.com/yourusername"
            ]
        },
        "summary": "Experienced software engineer with X years of experience in building scalable applications. Proficient in Java, Spring Boot, and cloud technologies.",
        "education": [
            {
                "institution": "University Name",
                "area": "Computer Science",
                "studyType": "Bachelor of Technology",
                "startDate": "2016",
                "endDate": "2020",
                "location": "City, State"
            }
        ],
        "experience": [
            {
                "company": "Current Company",
                "location": "City, State",
                "role": "Senior Software Engineer",
                "startDate": "Jan 2022",
                "endDate": "Present",
                "bullets": [
                    "Developed microservices using Spring Boot and Kafka, processing 10M+ events daily",
                    "Led migration from monolith to microservices architecture, reducing deployment time by 60%",
                    "Implemented CI/CD pipelines using Jenkins and Docker, achieving 99.9% uptime",
                    "Mentored team of 3 junior developers, conducting code reviews and technical sessions"
                ]
            },
            {
                "company": "Previous Company",
                "location": "City, State",
                "role": "Software Engineer",
                "startDate": "Jun 2020",
                "endDate": "Dec 2021",
                "bullets": [
                    "Built RESTful APIs serving 1M+ requests per day with Spring Boot and PostgreSQL",
                    "Optimized database queries reducing response time by 40%",
                    "Collaborated with cross-functional teams to deliver features on schedule"
                ]
            }
        ],
        "skills": [
            "Java", "Spring Boot", "Microservices", "Kafka", "PostgreSQL",
            "Docker", "Kubernetes", "AWS", "REST APIs", "Git",
            "CI/CD", "Agile", "Python", "JavaScript", "React"
        ],
        "projects": [
            {
                "name": "E-Commerce Platform",
                "techStack": "Java, Spring Boot, React, PostgreSQL, Docker",
                "description": "Built a scalable e-commerce platform handling 10K+ concurrent users with microservices architecture"
            }
        ],
        "achievements": [
            "Received 'Star Performer' award for Q3 2023",
            "Published technical blog with 10K+ monthly readers"
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_resume, f, indent=2)
    
    rprint(f"[green]✓[/green] Created: [bold]{output_path}[/bold]")
    rprint("\n[cyan]Next steps:[/cyan]")
    rprint("  1. Edit master_resume.json with your actual information")
    rprint("  2. Run: python main.py validate")
    rprint("  3. Run: python main.py apply <job_url> --api-key <key>")


if __name__ == "__main__":
    app()
