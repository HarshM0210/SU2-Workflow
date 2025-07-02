import os
import subprocess
import sys
from pathlib import Path
import shutil
from unittest import result 

def check_dependencies():
    """Verify SU2 and required files exist."""
    print(" Checking dependencies...")
    
    # Check SU2_CFD is available
    su2_cfd = shutil.which("SU2_CFD")
    if not su2_cfd:
        raise RuntimeError(
            "SU2_CFD not found in PATH. Is SU2 installed?\n"
            "Try running 'SU2_CFD --help' in terminal to verify."
        )
    
    # Python version check (3.11+)
    if sys.version_info < (3, 11):
        raise RuntimeError(f"Requires Python 3.11+. Detected: {sys.version}")
    
    print("All system dependencies verified.")

def check_files(config: Path, plot_script: Path, mesh_file: Path):
    """Verify required files exist."""
    missing = []
    if not config.exists():
        missing.append(config.name)
    if not plot_script.exists():
        missing.append(plot_script.name)
    if not mesh_file.exists():
        missing.append(mesh_file.name)
    
    if missing:
        raise FileNotFoundError(
            f"Missing files: {missing}\n"
            f"Current directory: {Path.cwd()}"
        )
    print(f" Found: {config.name}, {plot_script.name}, {mesh_file.name}")

def run_su2_simulation(config: Path):
    """Execute SU2_CFD"""
    print("\nStarting SU2 simulation...")
    try:
        result = subprocess.run(
            ["SU2_CFD", str(config)],
            cwd=config.parent,
            capture_output=True,
            text=True,
            check=True,
            timeout=3600
        )
        print("SU2 simulation succeeded.")
        print("\n=== SU2 Output ===")
        print(result.stdout)
        
        # Verify output file
        output_file = config.parent / "vol_solution.vtu"
        if not output_file.exists():
            raise FileNotFoundError(f"Expected output file not found: {output_file}")
            
    except subprocess.TimeoutExpired:
        print("SU2 timed out after 1 hour.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"SU2 failed (exit {e.returncode}). Last 20 lines:")
        print("\n".join(e.stdout.splitlines()[-20:]))
        print("\nError output:")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"SU2 simulation error: {e}")
        sys.exit(1)

def run_plot_script(script: Path):
    """Execute the Python plotting script."""
    print("\n Running post-processing...")
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=True
        )
        print("Plotting completed.")
        print("\n=== Plot Script Output ===")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Plot script failed (exit code {e.returncode}):")
        print(e.stderr)
        sys.exit(1)

def main():
    # Configurable filenames
    CONFIG_FILE = "config_sa.cfg"
    PLOT_SCRIPT = "plot.py"
    MESH_FILE = "047.su2"
    
    # Convert to absolute paths
    current_dir = Path.cwd()
    config_path = current_dir / CONFIG_FILE
    plot_path = current_dir / PLOT_SCRIPT
    mesh_path = current_dir / MESH_FILE

    print(f"\n=== SU2 Automation (Python {sys.version_info.major}.{sys.version_info.minor}) ===")
    
    try:
        check_dependencies()
        check_files(config_path, plot_path, mesh_path)
        run_su2_simulation(config_path)
        run_plot_script(plot_path)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
    
    print("\n Workflow completed successfully!")

if __name__ == "__main__":
    main()