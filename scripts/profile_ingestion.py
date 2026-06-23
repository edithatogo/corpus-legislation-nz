#!/usr/bin/env python
"""Profile the legislation ingestion and manifest writing pipelines."""

import cProfile
import pstats
import io
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nz_legislation_corpus.config import Settings
from nz_legislation_corpus.manifest import build_manifest
from nz_legislation_corpus.parquet_writer import write_partitioned_parquet
from nz_legislation_corpus.utils import read_jsonl
from rich.console import Console

console = Console()

# Create a minimal settings for profiling
class ProfileSettings:
    def __init__(self):
        # Use absolute path based on script location
        base = Path(__file__).parent.parent
        self.data_dir = base / "data"
        self.raw_dir = self.data_dir / "raw"
        self.records_jsonl_path = self.data_dir / "records.jsonl"
        self.manifests_dir = self.data_dir / "manifests"
        self.parquet_dir = self.data_dir / "parquet"


def profile_manifest_building():
    """Profile manifest building with existing data."""
    console.print("[bold cyan]Profiling manifest building...[/bold cyan]")
    settings = ProfileSettings()
    
    # Check if data exists
    if not settings.records_jsonl_path.exists():
        console.print("[yellow]No records.jsonl found, skipping manifest profiling[/yellow]")
        return
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run manifest building
    manifest = build_manifest(settings.data_dir, manifest_path=None)
    
    profiler.disable()
    
    # Output stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    console.print(s.getvalue())
    
    # Save to file
    output_path = Path("logs/profile_manifest.txt")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(s.getvalue())
    console.print(f"[green]Profile saved to {output_path}[/green]")


def profile_parquet_writing():
    """Profile parquet writing with existing data."""
    console.print("[bold cyan]Profiling parquet writing...[/bold cyan]")
    settings = ProfileSettings()
    
    if not settings.records_jsonl_path.exists():
        console.print("[yellow]No records.jsonl found, skipping parquet profiling[/yellow]")
        return
    
    records = read_jsonl(settings.records_jsonl_path)
    console.print(f"Loaded {len(records)} records")
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run parquet writing
    written = write_partitioned_parquet(records, settings.parquet_dir, overwrite=True)
    
    profiler.disable()
    
    # Output stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    console.print(s.getvalue())
    
    # Save to file
    output_path = Path("logs/profile_parquet.txt")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(s.getvalue())
    console.print(f"[green]Profile saved to {output_path}[/green]")


def main():
    """Run all profiling tasks."""
    console.print("[bold]Starting corpus-law-nz profiling[/bold]")
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run profiles
    profile_manifest_building()
    profile_parquet_writing()
    
    console.print("[bold green]Profiling complete![/bold green]")


if __name__ == "__main__":
    main()
