import subprocess
import sys
import os
import glob

print(" Script has started successfully!")


KICAD_CLI_PATH = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def run_kicad_cli(command, description):
    print(f"\n--- Running {description} ---")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"⚠️ CLI execution failed for {description} (Code: {result.returncode})")
            print("Error Output:\n", result.stderr)
        else:
            print(f" {description} report generated successfully.")
            
    except FileNotFoundError:
        print(f" Error: Could not find KiCad at {command[0]}")
        print("Please check if KiCad is installed in your Applications folder.")
        sys.exit(1)

if __name__ == "__main__":
    repo_dir = "AMS1117-Regulator-PCB"
    
    print(f"🔍 Searching for KiCad files in: {repo_dir}/")
    
    # Automatically find the first .kicad_sch and .kicad_pcb files in the folder
    sch_files = glob.glob(os.path.join(repo_dir, "*.kicad_sch"))
    pcb_files = glob.glob(os.path.join(repo_dir, "*.kicad_pcb"))

    # If it can't find them, it will print out exactly what is in the folder
    if not sch_files or not pcb_files:
        print(" Error: Could not find the schematic or PCB files in the repository.")
        if os.path.exists(repo_dir):
            print(f"Contents of {repo_dir}: {os.listdir(repo_dir)}")
        else:
            print(f"The folder '{repo_dir}' does not exist here.")
        sys.exit(1)

    # Assign the first matched files
    sch_file = sch_files[0]
    pcb_file = pcb_files[0]

    print(f" Found schematic: {sch_file}")
    print(f" Found PCB: {pcb_file}")

    # 1. Run Schematic ERC
    erc_command = [
        KICAD_CLI_PATH, "sch", "erc",
        "--format", "json",
        "--output", "erc_report.json",
        sch_file
    ]
    run_kicad_cli(erc_command, "Electrical Rules Check (ERC)")

    # 2. Run PCB Layout DRC
    drc_command = [
        KICAD_CLI_PATH, "pcb", "drc",
        "--format", "json",
        "--output", "drc_report.json",
        pcb_file
    ]
    run_kicad_cli(drc_command, "Design Rules Check (DRC)")
    
    print("\n Pipeline execution complete. Check your main directory for the .json reports.")